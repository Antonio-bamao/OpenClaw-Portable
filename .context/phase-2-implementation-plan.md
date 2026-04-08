# Phase 2｜实施计划

## 当前原则

- 先做 adapter 契约与测试，再接真实上游。
- 保持 UI 和 controller 稳定，避免 Phase 2 牵连 Phase 1 已完成界面。
- 先支持开发态真实 runtime，再收束到 U 盘交付态内置 Node。

## Step 1｜补测试入口

- 新增真实 runtime adapter 的测试文件。
- 先写失败测试，覆盖：
  - 缺少 `runtime/openclaw/` 时返回明确错误
  - Node 命令解析优先使用 `runtime/node/node.exe`
  - 环境变量合并必须继承系统环境
  - 日志路径指向 `%TEMP%\OpenClawPortable\logs\`
  - webui_url 使用 `PortResolver` 后的真实端口

验收：

- 已完成。新测试在实现前因缺少 `launcher.runtime.openclaw_runtime` 失败，符合 TDD RED 预期。

## Step 2｜新增 adapter 但不切默认运行时

- 新增 `launcher/runtime/openclaw_runtime.py`。
- 实现 `OpenClawRuntimeAdapter` 的最小骨架。
- 保持 `LauncherController` 默认仍使用 `MockRuntimeAdapter`，避免未接上游时破坏 Phase 1。

验收：

- 已完成。`tests.test_openclaw_runtime_adapter` 通过 4 个测试；完整测试套件通过 21 个测试。

## Step 3｜新增 runtime 选择策略

- 增加 runtime mode 配置或启动器内部开关。
- 开发态可选择 `mock` 或 `openclaw`。
- 默认仍可保持 `mock`，直到真实上游目录准备好。

验收：

- 已完成最小策略。未准备真实 OpenClaw 时默认仍为 mock；开发代码可通过 `LauncherController(runtime_mode="openclaw")` 切换真实 adapter。

## Step 4｜引入真实 OpenClaw 上游快照

- 下载或复制 OpenClaw `v2026.4.8` 到 `runtime/openclaw/`。
- 明确启动命令、健康检查 URL、所需环境变量。
- 记录上游启动事实到 `.context/decisions.md` 或单独接入记录。

验收：

- 已完成开发态验证。GitHub release zip 被确认为源码归档，最终改用 npm 构建包 `openclaw@2026.4.8`；安装生产依赖后，adapter 可启动真实 gateway 并完成 socket 健康检查。

## Step 5｜内置 Node 24 交付态准备

- 准备 `runtime/node/node.exe` 和必要运行文件。
- adapter 的 node 解析逻辑优先使用内置 Node。
- 打包脚本把 `runtime/node/`、`runtime/openclaw/` 纳入 dist。

验收：

- dist 产物不依赖系统 PATH 中的 node。
- 打包后能启动真实 runtime。

## Step 6｜UI 状态与错误文案收口

- 将 adapter 错误映射为中文可理解提示。
- 保留日志中的详细技术信息。
- 主面板展示真实 runtime 状态、端口、Provider、运行时长。

验收：

- 部分完成：启动器错误边界已将缺少运行时、启动超时、提前退出映射为中文可理解提示，并指向 `openclaw-runtime.err.log` 供售后排查；真实模式下 API Key 缺失会在主面板显示 Provider 名称与“重新配置”建议；主面板已开始渲染 `status_detail` 并展示运行时长；启动/重启时会先切换到“启动中 / 重启中”的等待状态并提示首启可能需要 20-60 秒。
- 待补充：进一步的 Provider 配置诊断。
- 非技术用户能理解“缺少运行时、端口冲突、Key 缺失、启动失败”的提示。
- 售后可以通过日志定位技术原因。

## Step 7｜回归与记录

- 运行完整单元测试。
- 运行真实 runtime 开发态烟雾测试。
- 运行 PyInstaller onedir 打包烟雾测试。
- 更新 `.context/work-log.md`、`.context/bug-log.md`、`.context/current-status.md`。

验收：

- 测试通过或失败项都有记录。
- `.context` 校验通过。
