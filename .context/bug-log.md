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

## OpenClaw adapter 测试把固定端口 18789 误当成永远空闲
- 现象：完整测试在 test_openclaw_runtime_adapter 中偶发失败，OPENCLAW_GATEWAY_PORT 和 status().port 断言到 18789，但实际解析到了 18790。
- 触发条件：运行 python -m unittest discover -s tests 时，宿主机上已有进程占用了 127.0.0.1:18789。
- 影响：完整测试结果受机器端口占用影响而不稳定，会掩盖真实回归结果并降低验证可信度。
- 根因：测试把固定端口写死为 18789，并隐含假设该端口永远可用；实际 adapter 契约允许 PortResolver 在端口被占用时回退到下一个可用端口。
- 解决方案：为 tests/test_openclaw_runtime_adapter.py 增加 reserve_free_port()，改用动态空闲端口构造配置和断言，避免依赖宿主机固定端口状态。
- 预防措施：后续凡是涉及端口的测试都优先使用动态空闲端口或显式占用/释放策略，不把固定端口当成可重复前提。
- 状态：Resolved

## 真实 OpenClaw 首次冷启动在 smoke 验证中逼近 60 秒超时阈值
- 现象：源码态和 dist 侧 smoke 的首次尝试都各出现过一次 OpenClaw runtime did not become healthy in time；保留日志后重跑，同样路径又能在约 20-31 秒内成功完成健康检查。
- 触发条件：Step 7 使用全新 tmp state 目录执行真实 OpenClawRuntimeAdapter 烟雾验证时触发。
- 影响：当前 60 秒等待窗口在冷启动边界上存在不确定性，会让便携包首启体验显得偶发失败，也影响 Step 7 烟雾结果的稳定性。
- 根因：初步证据指向真实 OpenClaw 在全新 state/logs/cache 环境下存在冷启动时延波动；首次尝试可能还要生成额外缓存或初始化插件，而后续同配置重试会显著变快。当前尚未确认是 runtime/openclaw 体积、磁盘热缓存还是其他 sidecar 初始化造成。
- 解决方案：先按 TDD 将真实 `OpenClawRuntimeAdapter` 默认等待窗口从 60 秒放宽到 90 秒，并把主界面启动等待提示同步改为 20-90 秒，作为用户体验层的缓解措施；冷启动根因定位仍继续保留在 Step 7。
- 预防措施：后续继续做 runtime/openclaw 瘦身、90 秒窗口下的首启耗时采样与 U 盘读写测试；当前实验性 `*.ts/*.mts/*.cts` 裁剪虽然单次 smoke 成功，但恢复正式默认规则后的 dist smoke 仍达到 58.49 秒，因此只有在有新的多轮 smoke 证据时才继续扩大或收紧等待策略，不凭感觉继续改 timeout。
- 状态：Mitigated

## append_work_log.py / record_bug.py 在当前 Windows 会话无法直接写入 `.context/*.md`
- 现象：运行 `append_work_log.py` 写 `.context/work-log.md`、运行 `record_bug.py` 写 `.context/bug-log.md` 时均报 `PermissionError: [Errno 13] Permission denied`。
- 触发条件：Phase 2 Step 31 补发布维护手册后，尝试通过 `project-context-os` 脚本追加工作日志和异常记录。
- 影响：本轮无法使用脚本追加 `.context` 记录，改为用同结构的最小 `apply_patch` 直接补记；产品代码与发布手册本身不受影响。
- 根因：文件属性显示不是只读，但 Windows 同时拒绝 Python `Path.write_text` 和 PowerShell `File.Open(..., ReadWrite, ...)` 对 `.context` markdown 文件的直接写打开；沙箱内 `Get-CimInstance Win32_Process` 又被拒绝，无法定位具体持锁进程。当前证据更像是编辑器、索引器或后台进程造成的环境级文件共享/权限限制，而不是 `.context` 内容格式问题。
- 解决方案：保留脚本失败证据，改用 `apply_patch` 按原结构写入 `work-log.md` 与 `bug-log.md`，随后执行 context 校验并确认 `context is valid`。
- 预防措施：后续若再次遇到该问题，先关闭可能持锁的编辑器/后台 git 或索引进程后重试脚本；若仍失败，只允许用最小范围结构化补记，并在日志中说明脚本写入失败原因。
- 状态：Documented

## GitHub Releases 更新源在 private 仓库下匿名访问返回 404
- 现象：`https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json` 与 tag 资产直链在发布后返回 404 / Not Found。
- 触发条件：`v2026.04.2` Release 已创建并上传资产，但仓库仍处于 private 状态；启动器和匿名 `Invoke-WebRequest` 不带 GitHub 登录态。
- 影响：在线更新源对真实用户不可用，启动器会把它表现为“无法连接更新服务器”或更新源不可达。
- 根因：GitHub private 仓库的 release 资产不能作为匿名公开更新源使用；`latest/download` URL 需要用户可匿名访问仓库和 release 资产。
- 解决方案：将仓库改为 public 后重新验证；`latest/download/update.json` 返回 200，zip 资产 HEAD 返回 200。
- 预防措施：后续若继续用 GitHub Releases 作为默认更新源，正式发布仓库必须保持 public；如果要保留 private 仓库，需要迁移到公开对象存储/静态站或实现带认证的更新源，但后者不适合小白用户便携版默认更新。
- 状态：Resolved

## 启动器长耗时按钮在 UI 主线程同步执行导致慢响应
- 现象：点击“检查更新”等按钮后响应很慢，多点几下后窗口容易进入“未响应”状态。
- 触发条件：真实 OpenClaw 启动、在线检查更新、下载 200MB 级 zip、导入更新包或恢复备份时，用户继续连续点击同一个按钮或其他长耗时按钮。
- 影响：虽然底层任务可能仍在执行，但用户会看到桌面窗口卡住，容易误以为程序崩溃，并可能把重复任务排进事件队列。
- 根因：`OpenClawLauncherApplication` 的启动、重启、检查更新、下载导入、导入更新包和恢复备份处理器直接在 PySide UI 主线程中同步调用 controller；慢网络、冷启动和文件复制都会阻塞 Qt 事件循环。
- 解决方案：为应用层加入后台执行器、完成 signal 和 busy action 集合；把长耗时动作移到后台线程执行，完成后再回到 UI 刷新或弹窗；主窗口在动作执行中禁用对应按钮并显示“正在...”文案。
- 预防措施：后续新增任何可能超过 200ms 的按钮动作，默认走后台任务或明确证明不会阻塞 UI；同时补重复点击保护测试和按钮 busy 态测试。
- 状态：Resolved

## 便携包审计初版误把依赖源码 cache 目录当成 U 盘写入风险
- 现象：运行 `python scripts/audit-portable-package.py --top 8` 时，报告把 `runtime/openclaw/node_modules/**/cache` 和 `runtime/openclaw/dist/extensions/**/node_modules/**/cache` 列为写入风险。
- 触发条件：审计工具按目录名匹配 `cache/logs/tmp`，但真实 OpenClaw runtime 的依赖源码中存在叫 `cache` 的代码目录。
- 影响：报告噪声较大，会误导后续优化方向，让我们以为依赖源码目录会在 U 盘运行时持续写入。
- 根因：写入风险规则没有区分“包内源码/依赖目录名”和“实际运行期可能写入的位置”；仅凭任意层级目录名匹配过宽。
- 解决方案：补回归测试，保留对包根、`state/` 和 `runtime/` 下非 `node_modules` 的写入风险提示，同时忽略所有 `node_modules` 内的同名代码目录。
- 预防措施：后续新增审计规则时要先用真实 dist 报告做一次 sanity check，避免把代码目录命名误判为运行期写入路径。
- 状态：Resolved

## 真实 dist smoke 后运行态 state 可能被误打进发布 zip
- 现象：当前 `dist/OpenClaw-Portable/state` 中出现 `openclaw.json`、`logs`、`tasks`、`workspace`、`canvas`、`channels`、`sessions`、`backups` 等运行态条目。
- 触发条件：对 `dist/OpenClaw-Portable` 执行真实 runtime smoke 后，OpenClaw 会把运行配置、健康检查日志、任务数据库和工作区目录写入 dist 下的 `state/`；如果随后手动调用 `scripts/build-release-assets.py` 对同一个 dist 打包，就可能把这些运行态文件带进 release zip。
- 影响：发布包可能包含开发机运行残留，既增加 U 盘写入和体积噪声，也可能混入不该交付给用户的状态文件。
- 根因：真实 smoke 的目标目录就是 dist 便携根目录，`state/` 作为便携用户数据目录会被正常写入；发布资产生成原先没有在 zip 前检查 `state/` 是否仍是干净模板态。
- 解决方案：在审计服务中新增 release state 清洁策略，只允许 `state/provider-templates`；发布 zip 生成前调用该策略，发现任何可变 state 条目就拒绝打包并列出路径。本地 `v2026.04.2` 已生成 zip 经验证仅包含 provider templates，未被污染。
- 预防措施：正式发版统一运行 `scripts/build-release-assets.ps1` 重新构建干净 dist；不要在真实 smoke 之后直接手动对同一个 dist 调 `scripts/build-release-assets.py`；如必须 smoke，smoke 后重新构建发布资产。
- 状态：Resolved

## runtime prune 实验入口与审计口径对 `test_artifacts` 不一致
- 现象：`python .\\scripts\\audit-portable-package.py --package-root dist\\OpenClaw-Portable --top 8` 报告 `test_artifacts` 为 `740` 个文件、约 `3.88MB`，但现有 `python .\\scripts\\prune-portable-runtime.py --runtime-path dist\\OpenClaw-Portable\\runtime\\openclaw --dry-run --pattern *.test.* --pattern *.spec.*` 只能命中 `338` 个文件、约 `2.27MB`。
- 触发条件：在 clean dist 上按 `.context` 的下一步执行 test artifacts 实验性 dry-run/裁剪时，同时依赖审计报告和 prune CLI 作为实验入口。
- 影响：我们无法用现有脚本完整复现实验目标，也就不能基于同一口径判断 `test_artifacts` 是否适合提升为默认 prune 规则。
- 根因：`portable_audit.py` 的 `test_artifacts` 规则除了文件名模式外，还把 `__tests__` / `test` 目录下的文件算入候选；而 `runtime_pruning.py` 只支持简单 glob pattern，不支持按目录名命中后代文件，因此漏掉了目录型测试产物。
- 解决方案：按 TDD 扩展 `tests/test_runtime_pruning.py`，随后在 `launcher/services/runtime_pruning.py` 增加目录名匹配能力，并让 `scripts/prune-portable-runtime.py` 新增实验性 `--directory-name` 参数；修复后 dry-run 与审计对齐为 `740` 个文件 / `3.88MB`。
- 预防措施：后续新增审计候选分组时，实验入口必须同步具备等价的命中语义；至少补一条“审计统计值与 prune dry-run 命中值一致”的回归验证，避免再次出现“报告可见、工具删不到”的半闭环。
- 状态：Resolved

## Delivery gate and tests interfered when run in parallel
- 现象：A full unittest run failed once in MockRuntimeAdapterTests.test_switches_to_next_port_when_requested_one_is_busy while a real runtime delivery gate was running in parallel; a later delivery gate run also hit a transient restart port bind failure before passing on rerun.
- 触发条件：Ran unit tests and a real OpenClaw runtime delivery gate concurrently, then immediately repeated runtime stability verification on randomly selected ports.
- 影响：Could produce false negative verification results and make the delivery flow look broken when the underlying feature code is not the root cause.
- 根因：The verification commands share localhost port space; real OpenClaw and mock runtime tests can interfere when executed concurrently, and OpenClaw can occasionally hit an internal port bind conflict on a randomly selected verification port.
- 解决方案：Stopped parallelizing unit tests with real runtime verification, reran tests serially, and reran the delivery gate serially; the full test suite passed and the second gate run passed local checks with only external evidence pending.
- 预防措施：Do not run real runtime stability gates in parallel with unit tests or other localhost runtime checks; keep delivery gate output as evidence and rerun isolated if a single port bind failure appears.
- 状态：documented
