# Bug / 工程异常记录

> 所有会影响推进、质量、节奏或判断的异常都要记录，包括代码、环境、依赖、测试、打包和设计误判。

## qfluentwidgets 商业授权风险
- 现象：最初计划使用 qfluentwidgets 提升桌面端高级感，但核对授权后发现商业化分发存在额外许可证要求。
- 触发条件：项目从演示原型转向可售卖 U 盘产品时，开始核对第三方 UI 组件库授权条款。
- 影响：如果继续使用存在商业授权限制的 UI 组件库，会给产品交付和开源策略带来法律与商业风险。
- 根因：前期只从界面效果角度选型，没有把商业授权约束和产品销售场景一起纳入评估。
- 解决方案：放弃 qfluentwidgets，改用原生 PySide6 与自定义主题体系重建界面。
- 预防措施：后续引入第三方依赖前，先做许可证与商业分发兼容性检查，并把结论写入 decisions.md。
- 状态：已解决

## Windows 临时目录权限与环境差异导致日志路径异常
- 现象：开发与测试过程中，日志和缓存目录在不同会话下表现不一致，导致部分验证对临时目录假设过强。
- 触发条件：在 Windows 本地与受限运行环境中同时验证 PortablePaths 和日志输出时出现路径可用性差异。
- 影响：如果路径策略不稳定，运行时日志无法可靠落盘，会影响健康检查、诊断包和售后定位。
- 根因：早期实现对临时目录权限与环境差异考虑不足，默认假设运行环境始终具备一致的临时目录写入条件。
- 解决方案：统一通过 PortablePaths 解析和创建日志目录，测试中改为显式准备可控目录，并避免依赖隐式环境假设。
- 预防措施：后续所有与路径相关的实现和测试都必须通过 PortablePaths 注入，不直接写死系统路径。
- 状态：已解决

## SO_REUSEADDR 导致端口占用判断失真
- 现象：端口检测在 Windows 上出现误判，部分被占用端口仍被视为可复用。
- 触发条件：为实现端口冲突自动处理而编写探测逻辑时，沿用了不适合当前场景的套接字复用策略。
- 影响：运行时可能尝试绑定实际不可用端口，造成启动失败或状态提示错误。
- 根因：把适用于部分网络场景的 SO_REUSEADDR 逻辑错误地用于端口可用性判断，没有充分考虑 Windows 平台差异。
- 解决方案：重写端口探测逻辑，以真实绑定能力为准，并在冲突时返回明确的新端口与提示文案。
- 预防措施：涉及端口与网络行为时，必须分别验证 Windows 语义，不能照搬跨平台默认经验。
- 状态：已解决

## Node 子进程未继承完整系统环境导致 runtime 启动失败
- 现象：mock runtime 曾出现 node 子进程可以拉起命令但无法稳定进入健康状态的情况。
- 触发条件：启动器通过 subprocess 创建 Node 运行时时，只传入了局部环境变量。
- 影响：运行时无法正常启动，主控制台状态和健康检查都会失真。
- 根因：子进程环境构造时覆盖了系统环境，遗漏 PATH 等基础变量，导致 Node 或相关依赖行为异常。
- 解决方案：启动 subprocess 时基于 os.environ 合并注入运行时变量，保证系统环境被保留。
- 预防措施：后续所有外部进程启动都默认以系统环境为基线，只追加项目所需变量。
- 状态：已解决

## 测试中写死端口导致环境相关失败
- 现象：部分测试在特定机器或会话中偶发失败，表现为端口已占用或运行时启动冲突。
- 触发条件：单元测试和集成验证早期直接使用固定端口，没有考虑开发机已有进程占用。
- 影响：测试结果不稳定，降低了对运行时行为与端口处理逻辑的信心。
- 根因：测试实现把环境前提写死了，缺少对动态端口分配和隔离的工程习惯。
- 解决方案：改为通过 PortResolver 或随机可用端口进行测试，避免固定端口依赖。
- 预防措施：后续所有需要网络端口的测试，都必须显式声明端口隔离策略。
- 状态：已解决

## GitHub CLI 远程发布时无法连通 github.com
- 现象：浏览器设备授权页面显示设备已连接，但 gh auth login 与后续发布流程仍失败，最近一次错误为无法连接 github.com。
- 触发条件：准备发布 project-context-os 到 GitHub 公开仓库时，通过本机 gh CLI 发起网页登录和状态校验。
- 影响：阻塞了 skill 仓库的远程创建与 push，导致目前只能先完成本地仓库和 OpenClaw 根目录 .context 的落地。
- 根因：当前机器或当前 CLI 运行环境对 github.com 的网络连通性不稳定，导致设备授权后的 token 交换与后续 API 访问失败。
- 解决方案：改用带 `repo` 与 `read:org` 范围的 Personal Access Token 建立 gh CLI 登录，随后重新执行 `gh auth status`、`gh api user` 与 `gh repo create` 完成发布。
- 预防措施：以后遇到需要远程发布的步骤，先做 gh auth status、gh api user 与基础连通性验证；若网页设备流不稳定，优先准备可用的 PAT 登录方案。
- 状态：已解决

## GitHub release zip 是源码归档且 npm 包缺少 node_modules
- 现象：GitHub release zip 缺少 dist/entry.js，无法直接作为运行时；改用 npm 包后 openclaw.mjs --help 可运行，但 gateway --help 因缺少 tslog 失败。
- 触发条件：Phase 2 尝试将 OpenClaw v2026.4.8 接入 runtime/openclaw 并执行真实 CLI 帮助命令。
- 影响：不能直接把 GitHub release zip 或裸 npm 包当作完整 U 盘 runtime，必须补齐构建产物与生产依赖，否则真实 gateway 无法启动。
- 根因：GitHub release zip 是源码快照，npm tarball 是构建包但不内置所有 runtime dependencies；OpenClaw CLI 子命令会动态导入依赖，需要 node_modules。
- 解决方案：保留 npm 构建包作为 runtime/openclaw 基础，在该目录运行 npm.cmd install --omit=dev 安装生产依赖，并完成 gateway 启动烟雾测试。
- 预防措施：后续 runtime 接入必须先验证 openclaw.mjs --help、gateway --help、gateway 启动三层，而不能只看 package.json 或 release 是否存在。
- 状态：已解决

## PowerShell npm.ps1 被执行策略拦截
- 现象：直接运行 npm --version 时，PowerShell 报 npm.ps1 cannot be loaded because running scripts is disabled。
- 触发条件：Phase 2 检查本机 npm 与 Node 环境时，在 PowerShell 中调用 npm。
- 影响：如果脚本直接调用 npm，可能在小白用户或干净 Windows 环境中失败，影响依赖安装和售后脚本。
- 根因：PowerShell 默认执行策略会拦截 npm.ps1，Windows 下 npm 同时提供 npm.cmd，后者不依赖 PowerShell 脚本执行权限。
- 解决方案：本轮所有 npm 操作改用 C:\Program Files\nodejs\npm.cmd。
- 预防措施：后续 Windows 脚本中调用 npm/pnpm/node 工具时优先使用 .cmd 或完整 exe 路径，避免依赖 PowerShell 执行策略。
- 状态：已解决

## OpenClaw runtime 复制到深层临时路径触发 Windows 长路径问题
- 现象：为了隔离真实 adapter 烟雾测试而复制 runtime/openclaw 到 tmp/openclaw-adapter-smoke-root 时，shutil.copytree 在嵌套 node_modules 路径上出现 WinError 206 文件名或扩展名太长。
- 触发条件：Phase 2 真实 adapter 烟雾测试尝试复制包含 dist/extensions/*/node_modules 的完整运行时目录。
- 影响：如果 U 盘目录层级过深或打包脚本复制路径过长，可能导致 runtime 文件丢失或打包失败。
- 根因：OpenClaw 生产依赖和 bundled extensions 中存在非常深的 node_modules 嵌套路径，Windows 默认路径长度限制容易被触发。
- 解决方案：烟雾测试改为引用当前 runtime_dir，只把 state/logs/cache 指向临时目录，不再复制整个 runtime 树。
- 预防措施：交付目录尽量保持短路径，例如 U 盘根目录 OpenClaw-Portable；打包脚本避免把 runtime 复制到过深临时目录；必要时评估长路径支持或依赖裁剪。
- 状态：已解决

## OpenClaw 首次真实启动需要更长健康检查窗口
- 现象：真实 gateway 首次启动约 18-25 秒后才监听端口，而 adapter 早期沿用 mock runtime 的 10 秒等待窗口会误判超时。
- 触发条件：Phase 2 用真实 OpenClaw gateway 执行受控启动烟雾测试。
- 影响：启动器可能在真实 runtime 仍在准备 Control UI 和插件时错误弹出启动失败。
- 根因：mock runtime 启动非常快，真实 OpenClaw 首次启动需要加载配置、生成 token、注册插件、准备 Control UI 和 sidecars。
- 解决方案：OpenClawRuntimeAdapter 增加 60 秒默认 startup_timeout_seconds，并将健康检查改为 gateway 端口 socket 探测。
- 预防措施：真实 runtime 的等待策略必须按真实启动曲线设置，不复用 mock runtime 的短等待假设。
- 状态：已解决

## 端口回退测试假设 occupied_port + 1 必定空闲
- 现象：完整测试偶发失败：PortResolverTests.test_moves_to_next_port_when_requested_port_is_occupied 期望返回 occupied_port + 1，但实际返回更后面的可用端口。
- 触发条件：本机临时端口池或其他进程刚好占用了测试 socket 后一个端口。
- 影响：测试结果依赖当前机器端口占用状态，导致 Phase 2 验证出现非确定性失败。
- 根因：测试把 PortResolver 的契约误写成必须选择 requested_port + 1；真实契约是从 requested_port + 1 开始向后扫描并返回第一个可用端口。
- 解决方案：将断言改为验证返回端口大于占用端口、位于 max_attempts 范围内，并且提示文案包含实际返回端口。
- 预防措施：后续端口相关测试避免假设相邻端口必定可用；如果确实要测试精确端口，必须显式占用或释放相关端口并控制扫描范围。
- 状态：Resolved

## PyInstaller onedir 后 Copy-Item 无法复制 OpenClaw node_modules 超长路径
- 现象：PyInstaller 构建成功后，build-launcher.ps1 在 Copy-Item runtime 目录时失败，报 Could not find a part of the path，路径指向 node_modules 内的深层测试快照文件。
- 触发条件：将真实 openclaw@2026.4.8 npm runtime 与完整生产依赖复制进 dist/OpenClaw-Portable 时触发。
- 影响：便携包无法完成构建，即使 launcher 本体已经由 PyInstaller 成功生成。
- 根因：PowerShell Copy-Item 在当前 Windows 路径与深层 node_modules 文件名组合下不适合复制大型 npm 依赖树，触发长路径相关复制失败。
- 解决方案：将打包脚本里的目录复制改为 Copy-DirectoryRobust，内部使用 robocopy /E 并对 exit code >= 8 判定失败。
- 预防措施：后续涉及 runtime/openclaw、node_modules 或其他深目录构建产物时优先使用 robocopy 或专门归档流程，不再用 Copy-Item 复制大型依赖树。
- 状态：Resolved

## 构建脚本清理旧 dist 时 Remove-Item 无法删除 OpenClaw 超长路径
- 现象：重新运行 build-launcher.ps1 时，在删除 dist/OpenClaw-Portable 阶段失败，Remove-Item 报 node_modules 深层快照文件路径不存在。
- 触发条件：前一次构建已经把完整 openclaw runtime 复制进 dist，下一次构建需要先清理旧 dist。
- 影响：即使 robocopy 已修复复制阶段，重复构建仍会在清理阶段失败，阻塞便携包持续验证。
- 根因：PowerShell Remove-Item 同样不适合处理当前 OpenClaw node_modules 的深层长路径文件树。
- 解决方案：新增 Remove-DirectoryRobust：先校验目标路径位于项目根目录内，再用 robocopy 空目录 /MIR 清空目标，最后删除空目录。
- 预防措施：构建脚本中涉及 dist/build/runtime 这类深目录清理时统一使用稳健删除函数，并保留根目录内路径校验。
- 状态：Resolved

## 在 PowerShell 中误用 Bash heredoc 验证命令
- 现象：运行 python - <<'PY' 验证 dist runtime mode 时，PowerShell 报 Missing file specification after redirection operator。
- 触发条件：从 Bash 习惯切换到当前 PowerShell shell 时，误用了 PowerShell 不支持的 heredoc 写法。
- 影响：单次验证命令失败，但没有影响源码、构建产物或运行时状态。
- 根因：shell 语法上下文判断错误；PowerShell 不支持 Bash 的 << heredoc 重定向语法。
- 解决方案：改用 PowerShell 兼容的 python -c 命令重新执行同一验证。
- 预防措施：后续在当前 Windows PowerShell 环境中避免使用 Bash heredoc；多行脚本使用 PowerShell here-string 管道或 python -c。
- 状态：Resolved

## VS Code 工作区扫描真实 runtime 生成产物导致 10 万级文件干扰
- 现象：IDE 工作区/源代码管理视图附近出现 10 万级文件噪声，影响继续查看真实源码改动。
- 触发条件：Phase 2 将 OpenClaw v2026.4.8 真实 runtime、生产依赖、内置 Node 和 onedir dist 产物保留在项目根目录下，用于便携包烟雾验证。
- 影响：Git 命令本身已经能通过 `.gitignore` 排除这些产物，但 IDE 仍可能对 `runtime/openclaw/`、`dist/`、`build/`、`tmp/`、`runtime/node/` 做文件树展示、搜索或 watcher 扫描，造成视觉噪声与性能压力。
- 根因：源码级忽略规则与 IDE 工作区扫描规则是两层机制；`.gitignore` 只能收敛 Git 可提交视图，不能自动禁止 VS Code 的 Explorer、搜索和文件监听扫描生成目录。
- 解决方案：新增项目级 `.vscode/settings.json`，在 `files.exclude`、`search.exclude` 和 `files.watcherExclude` 中排除 runtime/openclaw、runtime/node、dist、build、tmp、__pycache__ 与 .pytest_cache。
- 预防措施：后续只要在仓库内保留大型构建产物，必须同时维护 `.gitignore` 与 IDE workspace exclude；长期仍需要评估 runtime 瘦身或外置缓存策略。
- 状态：Resolved
