# 更新包数字签名设计
## 背景

项目当前已经具备以下更新可信度能力：
- 更新包版本校验
- `update-manifest.json` 离线 `SHA-256` 完整性校验
- 自动备份与失败回滚
- GitHub Releases 作为默认更新包托管源

这些能力已经能拦住空包、残包、损坏包和大多数被动过的包，但仍然缺少最后一层：

- 无法证明“这个包确实是发布者签出来的”
- 如果攻击者不仅篡改包内容，还能一起重写 `update-manifest.json`，当前链路仍无法区分“合法构建产物”和“伪造产物”

因此，本轮补的是“发布者身份可信度”。

## 目标

为便携版更新包补充 Ed25519 数字签名能力：

- 构建发布资产时对 `update-manifest.json` 做离线签名
- 便携包中新增签名文件
- 本地导入更新包和在线下载更新包时，先验签，再进入现有 manifest / 备份 / 替换 / 回滚链路
- 启动器内置公钥，只验证签名，不保存私钥

## 非目标

- 本轮不做 Windows 代码签名
- 本轮不做证书链或 CA 体系
- 本轮不做联网密钥托管
- 本轮不做多签名人 / 多公钥轮换策略
- 本轮不自动上传 GitHub Release

## 方案概览

采用 `Ed25519` + `PyNaCl`：

- 私钥仅用于发布侧签名
- 公钥写入仓库，用于运行时验签
- 签名对象不是整个 zip，而是 `update-manifest.json` 的原始字节

之所以签 `update-manifest.json`，是因为：
- manifest 已经覆盖关键分发条目的 `SHA-256`
- 只要 manifest 签名可信，且 manifest 校验通过，就能把“发布者身份”与“包完整性”串起来
- 不需要再把整个 zip 作为单独签名对象，能复用现有包内校验结构

## 依赖选择

新增 Python 依赖：

- `PyNaCl`

理由：
- 直接支持 Ed25519
- API 简单，适合当前项目体量
- 比手写纯 Python 实现风险更低

## 文件格式

便携包根目录新增：

- `update-signature.json`

建议结构：

```json
{
  "algorithm": "Ed25519",
  "keyId": "portable-ed25519-v1",
  "signature": "<base64-signature>"
}
```

字段规则：
- `algorithm`
  - 必填
  - 当前固定为 `Ed25519`
- `keyId`
  - 必填
  - 当前固定为单一 key id，便于后续做轮换时保留兼容空间
- `signature`
  - 必填
  - 对 `update-manifest.json` 原始字节做 Ed25519 detached signature 后的 base64 字符串

## 公钥与私钥管理

### 公钥

公钥作为运行时可信根，提交进仓库，建议集中在一个小模块中维护，例如：

- `launcher/services/update_signature.py`

其中包含：
- `DEFAULT_UPDATE_SIGNING_KEY_ID`
- `DEFAULT_UPDATE_SIGNING_PUBLIC_KEY`

### 私钥

私钥不进入仓库，默认放在本地忽略目录，例如：

- `.local/update-signing-private-key.txt`

并在 `.gitignore` 中显式忽略 `.local/`。

另外提供一个本地脚本，用于一次性生成 keypair：

- `scripts/generate-update-signing-keypair.py`

它负责：
- 生成 Ed25519 keypair
- 把私钥写到本地忽略目录
- 把公钥打印出来或同步到可复制的位置

本轮默认采用“单发布者、单 keypair”模式。

## 签名时机

签名发生在发布侧，而不是 `build-launcher.ps1` 基础构建阶段。

推荐流程：

1. `build-launcher.ps1`
   - 生成 `dist/OpenClaw-Portable/`
   - 生成 `update-manifest.json`
2. 发布资产构建脚本
   - 读取 `dist/OpenClaw-Portable/update-manifest.json`
   - 使用私钥生成 `update-signature.json`
   - 将签名文件写入 `dist/OpenClaw-Portable/`
   - 再打 zip、写 `update.json`

这样：
- 普通本地构建仍然可运行
- 真正用于更新分发的 release 包则强制带签名

## 验签顺序

在 `LocalUpdateImportService` 中，导入前顺序调整为：

1. 读取并校验 `version.json`
2. 校验版本必须严格高于当前版本
3. 验证 `update-signature.json`
4. 验证 `update-manifest.json`
5. 创建备份
6. 执行替换
7. 失败时回滚

这样一来：
- 签名不通过的包，会在任何文件替换前被拦住
- 篡改 manifest 的包，也会在 manifest 校验前先被签名层挡住

## 模块边界

建议新增共享模块：

- `launcher/services/update_signature.py`

职责：
- 维护默认 key id 与公钥
- 生成 keypair
- 读取私钥
- 对 manifest 字节签名
- 写出 `update-signature.json`
- 验证 `update-signature.json`

发布脚本只做编排，不自行处理签名算法。

## 脚本设计

### 1. `scripts/generate-update-signing-keypair.py`

职责：
- 生成一对 Ed25519 keypair
- 把私钥写到本地文件
- 输出公钥和 key id

### 2. `scripts/sign-update-manifest.py`

职责：
- 读取 `--package-root`
- 读取私钥路径
- 为 `update-manifest.json` 生成 `update-signature.json`

### 3. `scripts/build-release-assets.ps1`

职责增加：
- 在 zip 打包前调用 `sign-update-manifest.py`

默认私钥路径可设为：

- `.local/update-signing-private-key.txt`

如果私钥不存在，则发布脚本失败并提示先生成 keypair。

## 错误边界

### 发布阶段

- 私钥文件不存在时失败
- 私钥格式非法时失败
- `update-manifest.json` 缺失时失败
- 签名文件写入失败时失败

### 导入阶段

- 缺少 `update-signature.json` 时失败
- `algorithm` 不支持时失败
- `keyId` 不匹配时失败
- `signature` 非法 base64 时失败
- 验签失败时失败

错误文案应明确指向“数字签名校验失败”，而不是让用户误以为是普通坏包。

## 测试设计

### 签名模块

- 能生成 keypair
- 能对 manifest 字节签名
- 能成功验证合法签名
- 修改 manifest 后验签失败
- 非法 base64 签名时报错
- `keyId` 不匹配时报错

### 本地导入更新

- 缺少 `update-signature.json` 时失败
- 有效签名 + 有效 manifest 时可继续导入
- 篡改 manifest 后验签失败
- 错误 key 签名时失败

### 发布脚本相关

- 能为测试包目录写出 `update-signature.json`
- release 资产构建后 zip 内包含 `update-signature.json`

## 取舍

- 选择签 manifest，而不是签整个 zip：
  - 复用现有 manifest 结构
  - 与当前本地导入校验链路更贴合
  - 减少重复校验面
- 选择 Ed25519，而不是 RSA：
  - 更轻量
  - 密钥和签名更短
  - 更适合当前单发布者场景
- 选择仓库内置公钥 + 本地忽略私钥：
  - 运行时简单
  - 不依赖联网密钥服务
  - 与 GitHub Releases 的离线分发模型一致
