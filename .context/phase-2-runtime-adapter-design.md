# Phase 2｜真实 OpenClaw Runtime Adapter 设计

## 设计结论

Phase 2 默认采用 **原生 Windows 便携运行时**：

- 默认交付模式：Windows 10/11 x64 原生运行
- Node 版本策略：Node 24 优先，Node 22.14+ 仅作为兼容备选
- OpenClaw 版本策略：优先锁定 GitHub Release `v2026.4.8`
- WSL2 策略：只作为高级用户或排障 fallback，不进入默认 U 盘交付流程
- 适配边界：保留现有 `RuntimeAdapter` 接口，新增真实 runtime adapter，不重写 UI 和 controller

依据：

- 本项目原始产品文档要求“插上即用、双击启动、WebUI 操作、零命令行”，目标用户是非技术用户。
- U 盘版必须尽量避免管理员权限、WSL 安装、虚拟化开关、公司/学校电脑策略限制等外部前提。
- 官方 Getting Started 当前建议 Node 24，且 Windows 原生与 WSL2 都可用；对便携商业交付来说，原生 Windows 的售后面更小。

官方参考：

- https://github.com/openclaw/openclaw/releases
- https://github.com/openclaw/openclaw/blob/main/docs/start/getting-started.md

## 目标

- 让 `OpenClawLauncher.exe` 能启动真实 OpenClaw gateway，而不是 Phase 1 的 Node mock runtime。
- 保持 `LauncherController`、主控制台、首次向导的外部行为稳定。
- 将真实 OpenClaw 的配置、状态、日志、缓存导向便携目录。
- 为 Phase 3 渠道插件和 Phase 4 诊断更新能力预留稳定接口。

## 非目标

- 不在 Phase 2 默认引入 WSL2。
- 不在 Phase 2 做渠道插件完整接入。
- 不在 Phase 2 做自动更新与回滚完整系统。
- 不在 Phase 2 把 UI 重写成新的框架或新布局。

## 目录结构

目标交付结构：

```text
runtime/
  node/
    node.exe
    ...
  openclaw/
    package.json
    node_modules/
    ...
  plugins/
state/
  openclaw.json
  .env
  workspace/
  sessions/
  channels/
  backups/
%TEMP%\OpenClawPortable\
  logs/
  cache/
```

Phase 2 实施中先允许使用开发态 `node` 命令和 `runtime/openclaw/` 源码目录；打包态再切换到 `runtime/node/node.exe`。

## Adapter 设计

新增 `OpenClawRuntimeAdapter`，继续实现现有接口：

- `prepare(config, paths)`
- `start()`
- `stop()`
- `restart()`
- `status()`
- `webui_url()`
- `healthcheck()`

Adapter 负责：

- 解析 OpenClaw 入口脚本或 npm 启动命令
- 准备运行时环境变量
- 写入日志到 `%TEMP%\OpenClawPortable\logs\`
- 将工作目录固定到 `runtime/openclaw/`
- 继承系统环境后追加项目变量
- 检查进程是否提前退出
- 健康检查失败时返回可解释错误

## 环境变量策略

真实变量名需要在接入上游代码时按实际要求确认。Phase 2 先建立我们自己的适配层变量映射表：

- `OPENCLAW_PORT`：由 `PortResolver` 解析后的实际端口
- `OPENCLAW_BIND_HOST`：默认 `127.0.0.1`
- `OPENCLAW_STATE_DIR`：指向 `state/`
- `OPENCLAW_WORKSPACE_DIR`：指向 `state/workspace/`
- `OPENCLAW_LOG_DIR`：指向 `%TEMP%\OpenClawPortable\logs\`
- `OPENCLAW_CACHE_DIR`：指向 `%TEMP%\OpenClawPortable\cache\`
- `OPENCLAW_API_KEY`：从 `state/.env` 读取后传给子进程，不写入 `openclaw.json`
- Provider 相关变量：由 `LauncherConfig` 转换，具体命名按上游 runtime 要求适配

如果上游不支持这些变量，需要在 adapter 内生成上游实际配置文件，但生成结果仍必须落在 `state/` 或 `%TEMP%\OpenClawPortable\` 中。

## 启动命令策略

Phase 2 分两层推进：

1. 开发态
   - 使用系统 `node` 或包管理器命令启动 `runtime/openclaw/`
   - 目的是验证 adapter、路径、端口和健康检查
2. 交付态
   - 使用 `runtime/node/node.exe`
   - 启动命令不得依赖全局 PATH
   - 打包时必须把 `runtime/node/` 和 `runtime/openclaw/` 放入 dist

## 健康检查

Adapter 优先使用上游官方健康检查接口；如果上游没有稳定 `/health`，则按以下顺序降级：

1. 请求 WebUI 根路径，确认 HTTP 200/30x
2. 检测端口监听与进程存活
3. 读取 stderr 日志中的启动失败关键字

健康检查返回 `RuntimeHealth`，不把底层异常直接暴露给 UI。

## 错误处理

必须覆盖：

- `runtime/openclaw/` 缺失
- `node.exe` 缺失或版本不符合要求
- 端口被占用并自动切换
- 子进程提前退出
- 健康检查超时
- Provider 配置缺失或 API Key 为空
- 上游启动命令变更

错误文案要面向非技术用户，但日志中保留足够排障信息。

## 测试策略

先测 adapter 边界，再测真实 runtime：

- 单元测试：命令解析、环境变量合并、路径生成、状态映射、错误分支。
- 契约测试：`MockRuntimeAdapter` 和 `OpenClawRuntimeAdapter` 都满足 `RuntimeAdapter` 外部行为。
- 开发态集成测试：在 `runtime/openclaw/` 存在时可启动真实服务并健康检查。
- 打包烟雾测试：`PyInstaller onedir` 产物能找到 `runtime/node/node.exe` 与 `runtime/openclaw/`。

## 验收标准

- 主控制台不改大结构即可切换真实 runtime。
- 双击启动器后可启动真实 OpenClaw 服务。
- WebUI 地址来自真实绑定端口。
- 日志与缓存不写入 U 盘高频路径。
- `state/openclaw.json` 不包含敏感 Key。
- 失败时 UI 显示可理解错误，日志保留技术细节。
