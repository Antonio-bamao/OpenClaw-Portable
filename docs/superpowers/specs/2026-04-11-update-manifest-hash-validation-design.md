# 本地更新包 `update-manifest.json` 哈希校验设计

## 背景

当前项目已经具备：

- 本地导入更新包
- 更新前自动备份
- 中途失败自动回滚
- 从更新备份恢复旧版本
- “导入更新包”严格只接受更高版本

但“更新包是不是完整、有没有被动过”这一层可信度仍然缺失。仅靠 `version.json` 和目录结构，无法识别下载损坏、拷贝损坏或被手工替换过的关键文件。

## 目标

为本地更新包增加离线完整性校验：

- 打包产物自动生成 `update-manifest.json`
- 导入更新包前强制校验 manifest 结构和关键内容的 `SHA-256`
- 任一关键条目缺失、未登记或哈希不匹配时，直接拦截

## 非目标

- 本轮不做联网签名验证
- 本轮不做证书签名
- 本轮不实现“检查更新”联网接口
- 本轮不把 manifest 应用于“恢复更新备份”路径

## 包格式

更新包根目录新增：

- `update-manifest.json`

manifest 至少包含：

- `manifestVersion`
- `packageVersion`
- `generatedAt`
- `entries`

其中 `entries` 是一个对象，键为相对路径，值为：

- `type`: `file` 或 `dir`
- `sha256`: 文件内容或目录内容摘要

## 校验范围

继续只覆盖当前允许更新的分发内容：

- `OpenClawLauncher.exe`
- `_internal`
- `runtime`
- `assets`
- `tools`
- `README.txt`
- `version.json`

manifest 必须至少覆盖除 `version.json` 外的一项真实分发内容，且导入流程中实际参与替换的每个条目都必须有 manifest 记录。

## 哈希规则

### 文件

- 读取原始字节流
- 计算 `SHA-256`

### 目录

目录摘要必须稳定且与拷贝顺序无关，建议规则：

1. 递归枚举目录内所有文件
2. 使用相对路径排序
3. 对每个文件计算 `sha256`
4. 用 `相对路径 + 文件哈希` 组合出规范化文本
5. 对整段规范化文本再做一次 `SHA-256`

这样即使目录很大，也能在不依赖打包顺序的前提下得到稳定摘要。

## 方案

### 生成侧

新增一个可复用的 Python 模块，负责：

- 计算文件/目录哈希
- 为给定便携包根目录生成 `update-manifest.json`
- 供构建脚本和导入校验共用

`scripts/build-launcher.ps1` 在复制完分发内容、裁剪完 runtime 后，最后生成 `dist/OpenClaw-Portable/update-manifest.json`。

### 校验侧

`LocalUpdateImportService.import_package()` 在现有版本/结构校验之后、创建备份之前，再增加 manifest 校验：

- `update-manifest.json` 必须存在
- manifest 必须是合法 JSON
- `packageVersion` 必须与 `version.json.version` 一致
- 每个实际可导入条目都必须在 manifest 中登记
- 每个登记条目的 `type` 和实际文件系统对象必须匹配
- 每个登记条目的 `sha256` 必须与实物一致

只要有一个不匹配，就直接失败，不进入备份和替换流程。

## 错误文案

建议最小文案：

- `更新包缺少 update-manifest.json。`
- `更新包的 update-manifest.json 不是合法 JSON。`
- `更新包的完整性清单缺少有效版本号。`
- `更新包版本信息与完整性清单不一致。`
- `更新包缺少必要的完整性记录：{entry}`
- `更新包完整性校验失败：{entry}`

文案应保持面向用户，不暴露过多底层细节。

## 测试

- 哈希模块测试：
  - 同一文件内容哈希稳定
  - 同一目录在相同内容下摘要稳定
  - 目录内文件变动会改变摘要
  - manifest 生成后包含预期条目
- 本地更新测试：
  - 完整且合法的 manifest 可通过导入
  - 缺少 manifest 时失败
  - manifest 非法 JSON 时失败
  - manifest 版本与 `version.json` 不一致时失败
  - 关键文件被篡改后哈希不匹配时失败
  - 缺少某个可导入条目的 manifest 记录时失败
- 构建侧测试：
  - 生成 manifest 的模块测试通过即可；构建脚本本身以最小集成改动接入

## 取舍

- 哈希清单不能像数字签名那样证明“发布者身份”，但它已经足够解决“小白用户误拿坏包 / 半包 / 被动过的包”这一层现实问题。
- 相比先做联网检查更新，离线哈希校验更贴近当前已有的“手动导入更新包”链路，也更容易在不引入服务端的情况下真正提升可信度。
