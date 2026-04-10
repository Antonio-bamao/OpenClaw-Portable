# 决策记录

> 记录高影响决策，不要只记录结论，要写背景、理由和后续约束。

## 2026-04-07｜桌面端技术栈改为原生 `PySide6 + 自定义主题`

- 背景：最初考虑 `qfluentwidgets` 以快速获得更强的 Fluent 风格组件，但项目目标包含商业化出售 U 盘成品。
- 理由：为避免商业授权与 GPL 风险，改用原生 `PySide6` 并自己建立视觉体系；这样可以保留商业分发自由度，同时仍能做出高级感 UI。
- 影响范围：所有桌面端 UI、打包依赖、后续主题扩展方式。
- 后续约束：新增 UI 组件时优先复用已有主题与自定义控件，不重新引入存在商业授权风险的第三方 UI 组件库。

## 2026-04-07｜Phase 1 运行时使用 Node mock runtime，而不是 Python 假服务

- 背景：Phase 1 只需要一个可联调、可健康检查的开发版 runtime，但后续一定会接真实 OpenClaw。
- 理由：用 Node mock runtime 更接近未来真实 runtime 的进程模型、端口模型和日志模型，能降低后续替换成本。
- 影响范围：`MockRuntimeAdapter`、健康检查、日志输出、打包目录结构、测试策略。
- 后续约束：controller 与 UI 必须只依赖 `RuntimeAdapter` 接口，不允许直接耦合 mock 细节。

## 2026-04-07｜首版打包策略固定为 `PyInstaller onedir`

- 背景：桌面端需要尽快得到可交付、可验收的构建结果，同时避免过早陷入 onefile 的排障成本。
- 理由：`onedir` 更利于 `PySide6` 和未来 Node/runtime 目录的分发与排障，也更符合“便携目录可见、结构明确”的产品形态。
- 影响范围：构建脚本、分发目录结构、测试与售后排障方式。
- 后续约束：在 Phase 2/4 之前不追求 onefile；优化重点放在稳定性与目录完整性，而不是单文件美观。

## 2026-04-07｜Provider 采用 JSON 模板注册机制

- 背景：首版需要内置通义千问、DeepSeek、OpenRouter、自定义，后续还会增加更多 Provider 或更新默认模型。
- 理由：将模板外置到 `state/provider-templates/`，便于后续迭代、差异化分发和最小化 UI 层改动。
- 影响范围：引导流程、Provider 下拉、配置默认值、后续升级逻辑。
- 后续约束：模板格式变更必须保持向后兼容，避免影响已写入 `state/openclaw.json` 的用户配置。

## 2026-04-07｜OpenClaw 仓库进入 `.context` 驱动的实施模式

- 背景：项目已经从单纯构思进入真实实施，如果继续靠临时对话和零散设计文档推进，后续阶段会快速失去连续性。
- 理由：引入 `project-context-os` 作为工程操作系统，强制维护总体计划、当前状态、工作日志、Bug 台账、决策记录和风险台账。
- 影响范围：后续所有功能开发、Bug 修复、发布准备与售后能力建设。
- 后续约束：开始真实实施前必须先读并更新 `.context`；完成明确步骤后必须及时补日志。

## 2026-04-08｜Phase 2 默认采用原生 Windows 运行时，不把 WSL2 作为 U 盘版默认方案

- 背景：官方文档说明 Windows 原生与 WSL2 都可用，并推荐 Node 24；同时提到 WSL2 在部分场景更稳定。但本项目是面向非技术用户的 U 盘便携版，原始产品定位是“插上即用、双击启动、零命令行”。
- 理由：WSL2 依赖虚拟化、系统组件安装、管理员权限和用户机器策略，容易在公司/学校电脑或小白用户环境中造成售后爆炸；原生 Windows + 内置 Node 更符合 U 盘交付。
- 影响范围：Phase 2 runtime adapter、打包脚本、售后文档、风险台账与后续环境检测。
- 后续约束：默认交付链路必须优先使用 `runtime/node/node.exe` 与 `runtime/openclaw/`；WSL2 只能作为高级 fallback，不得成为默认启动路径。

## 2026-04-08｜Phase 2 优先锁定 OpenClaw `v2026.4.8` 与 Node 24

- 背景：进入 Phase 2 时需要锁定上游快照，避免接入过程中跟随上游 main 分支漂移。
- 理由：Release 版本更适合便携产品验证与回归；Node 24 是当前官方 Getting Started 的推荐版本。
- 影响范围：`runtime/openclaw/` 内容、`runtime/node/` 内容、真实 adapter 启动命令、打包烟雾测试。
- 后续约束：升级上游版本必须通过 `.context` 记录决策，并补齐打包与健康检查回归。

## 2026-04-08｜OpenClaw runtime 使用 npm 构建包而不是 GitHub release zip 源码归档

- 背景：GitHub release zip `v2026.4.8` 缺少 `dist/entry.js`，`openclaw.mjs` 会提示这是未构建源码树；npm 包 `openclaw@2026.4.8` 包含 `dist/` 构建产物。
- 理由：U 盘版应携带可直接运行的构建包，避免在用户机器上执行 `pnpm install && pnpm build`。
- 影响范围：`runtime/openclaw/` 目录来源、依赖安装方式、打包体积、后续升级策略。
- 后续约束：Phase 2 以后优先使用 npm 发布包作为 runtime 基线；如果改用源码构建，必须记录构建命令、构建产物和可复现验证。

## 2026-04-08｜真实 gateway 健康检查先使用端口 socket 探测，WebUI URL 指向控制端口

- 背景：OpenClaw gateway 真实启动命令为 `openclaw gateway run --port <port> --bind loopback --allow-unconfigured`；gateway 端口不是 Control UI 端口，启动日志显示 Control UI 监听在 `gatewayPort + 2`。
- 理由：早期用 HTTP `/health` 判断不适合真实 gateway；先用 socket 探测确认 gateway 端口可连接，更贴近当前可验证行为。
- 影响范围：`OpenClawRuntimeAdapter.healthcheck()`、`OpenClawRuntimeAdapter.webui_url()`、主控制台“打开 WebUI”行为。
- 后续约束：如果后续确认稳定 RPC health 接口，应将 socket 探测升级为 RPC health，但仍保留端口探测作为 fallback。

## 2026-04-08｜`runtime/openclaw/` 作为构建产物，不提交进源码仓库

- 背景：`openclaw@2026.4.8` 安装生产依赖后约 1GB 且包含大量 `node_modules` 与 bundled extension 依赖，直接提交会让源码仓库膨胀、审查困难，并增加 GitHub 推送与后续维护成本。
- 理由：U 盘版最终需要携带完整 runtime，但源码仓库更适合保存 adapter、锁定版本、准备脚本与打包规则；真实 runtime 由 `scripts/prepare-openclaw-runtime.ps1` 在构建/交付前生成。
- 影响范围：`.gitignore`、打包脚本、构建流程、发布说明、后续 CI/离线打包策略。
- 后续约束：任何需要构建便携包的流程必须先验证 `runtime/openclaw/openclaw.mjs` 与 `runtime/openclaw/dist/entry.js` 存在；如果要改为提交 runtime 产物，必须重新评估仓库体积、许可证、供应链和升级策略。

## 2026-04-08｜内置 Node 24 作为构建产物随便携包分发

- 背景：OpenClaw `v2026.4.8` 要求 Node `>=22.14.0`，官方推荐 Node 24；U 盘版不能要求小白用户预先安装 Node。
- 理由：将 `runtime/node/node.exe` 作为本地构建产物准备并打入 dist，可让真实 OpenClaw gateway 使用便携目录内的 Node，而不是依赖用户机器环境。
- 影响范围：`OpenClawRuntimeAdapter.resolved_node_command()`、`scripts/prepare-node-runtime.ps1`、`.gitignore`、`scripts/build-launcher.ps1`、U 盘交付体积。
- 后续约束：源码仓库不提交 Node 二进制；构建便携包前必须运行 `scripts/prepare-node-runtime.ps1`，且 Node 版本必须保持 v24 系列，除非重新记录兼容性决策。

## 2026-04-08｜启动器使用 auto runtime mode，完整便携包默认进入真实 OpenClaw

- 背景：Phase 1 默认 mock 运行时利于开发，但 U 盘成品必须双击后进入真实 OpenClaw；如果硬编码成 openclaw，则缺 runtime 的开发环境会更容易报错。
- 理由：auto 策略可以同时满足开发和交付：检测到 `runtime/openclaw/openclaw.mjs` 与 `runtime/node/node.exe` 时使用真实 OpenClaw，否则回退 mock；同时保留 `OPENCLAW_PORTABLE_RUNTIME_MODE` 环境变量和显式参数覆盖能力。
- 影响范围：`OpenClawLauncherApplication` 启动策略、开发调试、PyInstaller dist 行为、售后排障。
- 后续约束：后续如果新增 UI 设置项或命令行参数切换 runtime mode，必须继续复用 `resolve_runtime_mode()`，避免多处判断漂移。

## 2026-04-10｜便携包 dist 默认裁剪 `runtime/openclaw` 中的 `.map`、`.md` 与 `.d.ts`

- 背景：Step 7 量化后发现 `runtime/openclaw` 约 0.992GB，其中 `.map` 与 `.md` 约 127MB，而 `*.d.ts` 另占约 115.75MB；这三类文件都更偏发布冗余或类型声明，比直接动 plain `.ts` 更稳妥。
- 理由：source runtime 仍保留完整产物，便于后续排障和进一步分析；而便携包 dist 更关注体积与拷贝成本，移除 source map 与 markdown 文档对运行时行为影响最小。
- 理由：source runtime 仍保留完整产物，便于后续排障和进一步分析；而便携包 dist 更关注体积与拷贝成本，移除 source map、markdown 文档与 TypeScript 类型声明对运行时行为影响最小。
- 影响范围：`scripts/build-launcher.ps1`、`scripts/prune-portable-runtime.py`、便携包体积、后续 smoke 验证流程。
- 后续约束：当前仅允许自动裁剪 `.map`、`.md` 与 `.d.ts`；若要继续裁剪 plain `.ts`、`.mts`、`.cts`、测试快照或其他候选文件，必须先补 smoke/回归证据，不得直接扩大裁剪范围。
