# GitHub Releases 更新包发布设计
## 背景

项目已经具备以下更新能力：
- 本地导入更新包
- 严格版本校验
- `update-manifest.json` 离线完整性校验
- 自动备份与失败回滚
- 在线检查更新、下载 zip、解压到临时目录并交给本地导入链路
- 更新源 URL 的集中解析与环境变量覆盖

当前剩下的最后一层缺口是“发布侧”：
- 还没有一条面向 GitHub Releases 的标准化发布流程
- 默认更新源地址仍是占位值
- 构建产物还不会自动生成发布用 zip 与 `update.json`

这导致“检查更新”主链路虽然已经可用，但还没有真正连上稳定、低成本、适合个人项目的发布源。

## 目标

本轮把 GitHub Releases 作为便携版更新包托管方式正式接入：

- 自动把 `dist/OpenClaw-Portable/` 打成发布用 zip
- 自动生成可直接上传到 GitHub Release 的 `update.json`
- 将应用内置默认更新源改为当前仓库的：
  - `https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json`
- 保持现有在线更新导入链路不变：仍然只下载 zip、解压到临时目录，再交给本地导入更新逻辑

## 非目标

- 本轮不直接调用 GitHub API 自动创建 Release
- 本轮不自动上传资产到 GitHub
- 本轮不实现数字签名
- 本轮不解析 OpenClaw 上游官方 release 并直接替换便携版
- 本轮不增加 GUI 中的发布配置页面

## 发布模型

每个便携版发布对应一个 GitHub Release。

每个 Release 至少包含两个资产：
- `OpenClaw-Portable-<version>.zip`
- `update.json`

其中：
- zip 是真正下载给用户的更新包
- `update.json` 是应用“检查更新”时请求的元数据入口

应用内置默认 feed 固定读取：

`https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json`

这样，用户永远只需要访问“最新 Release 的 update.json”，而不需要知道具体 tag。

## `update.json` 结构

本轮沿用现有在线更新格式：

```json
{
  "version": "v2026.04.2",
  "notes": [
    "升级 OpenClaw runtime",
    "修复本地更新流程"
  ],
  "packageUrl": "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.2/OpenClaw-Portable-v2026.04.2.zip"
}
```

字段规则：
- `version`
  - 必填
  - 必须与便携包内 `version.json.version` 一致
- `notes`
  - 选填
  - 缺省时按空数组处理
- `packageUrl`
  - 必填
  - 指向当前仓库对应 tag 下的 zip 资产

## 产物生成策略

建议新增一个独立的“发布资产构建”脚本，而不是把所有逻辑继续塞进 `build-launcher.ps1`。

### 1. `build-launcher.ps1`

职责继续保持不变：
- 构建 `dist/OpenClaw-Portable/`
- 复制 runtime / assets / tools / `version.json`
- 裁剪 runtime
- 生成 `update-manifest.json`

### 2. `build-release-assets.ps1`

新增一条面向发布的脚本：
- 先调用 `build-launcher.ps1`
- 再把 `dist/OpenClaw-Portable/` 打成 zip
- 再生成 `dist/release/update.json`
- 最终输出：
  - `dist/release/OpenClaw-Portable-<version>.zip`
  - `dist/release/update.json`

### 3. Python 侧共享发布元数据模块

建议把以下逻辑提炼到一个可测试的 Python 模块中：
- 读取 `version.json`
- 生成 zip 资产文件名
- 拼装 GitHub Releases 的下载 URL
- 生成 `update.json`

这样 PowerShell 只负责编排，核心逻辑集中在 Python 中做单元测试。

## 默认更新源

`launcher/services/update_feed.py` 中的默认 feed 地址改为：

`https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json`

仍保留当前优先级：
1. 显式传入 URL
2. 环境变量 `OPENCLAW_PORTABLE_UPDATE_FEED_URL`
3. 内置默认地址

这样：
- 正式用户开箱即用
- 本地联调和灰度仍然可以切换 feed

## ZIP 结构要求

zip 内必须保留便携包根目录，例如：

```text
OpenClaw-Portable/
  OpenClawLauncher.exe
  version.json
  update-manifest.json
  runtime/
  assets/
  tools/
```

原因：
- 现有在线更新解压后会递归查找同时包含 `version.json` 和 `update-manifest.json` 的包根目录
- 保留顶层目录更符合便携包分发习惯，也能避免把所有文件平铺到临时目录根部

## 发布者操作流程

每次发版时，维护者执行：

1. 运行发布资产构建脚本
2. 获取 `dist/release/OpenClaw-Portable-<version>.zip`
3. 获取 `dist/release/update.json`
4. 在 GitHub 上创建对应 tag 的 Release
5. 上传上述两个资产

发布完成后：
- 应用检查 `releases/latest/download/update.json`
- 读到其中的 `packageUrl`
- 下载对应 tag 下的 zip

## 错误边界

### 构建阶段

- `version.json` 缺失或无法解析时失败
- 便携包目录不存在时失败
- zip 创建失败时失败
- `update.json` 写入失败时失败

### 运行时

本轮不新增新的运行时错误类型，仍复用现有在线更新错误边界：
- 更新源不可达
- `update.json` 非法
- zip 下载失败
- zip 解压失败
- 导入链路中的版本 / manifest / 备份 / 替换 / 回滚失败

## 测试设计

### 发布元数据模块

- 默认更新源 URL 指向当前仓库的 GitHub Releases latest/download 地址
- 生成的 zip 资产文件名符合 `OpenClaw-Portable-<version>.zip`
- 生成的 `packageUrl` 指向 `releases/download/<tag>/<asset>`
- 生成的 `update.json` 中版本号与包地址正确

### 发布资产构建

- 能把一个最小测试包目录打成 zip
- zip 内保留 `OpenClaw-Portable/` 顶层目录
- 能写出 `update.json`

### 在线更新回归

- 默认 feed 地址切换后，现有解析逻辑仍可工作
- 环境变量覆盖仍优先于默认地址

## 取舍

- 选择 GitHub Releases，而不是自建服务器：
  - 成本更低
  - 足够支撑当前便携版更新分发
  - 与项目当前 GitHub 仓库天然匹配
- 选择“生成发布资产但不自动上传”：
  - 风险更低
  - 不需要在本地脚本里引入 GitHub Token 与发布权限
  - 对当前阶段已经足够
- 选择仓库自己的 Release，而不是直接链接 OpenClaw 上游官方发布：
  - 便携版不是原始 OpenClaw 结构
  - 当前更新链路依赖自有 `version.json` 与 `update-manifest.json`
  - 直接吃上游包会破坏启动器与便携目录边界
