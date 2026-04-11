# 工作日志

> 每完成一个明确步骤就追加一条记录，不写流水账。

## 2026-04-07 / Step 01｜初始化仓库与便携目录骨架
- 目标：初始化仓库与便携目录骨架
- 动作：建立 git 仓库、梳理 runtime state assets tools 目录、固定便携路径策略并落基础元数据。
- 结果：OpenClaw Portable 具备了 Phase 1 单仓便携壳层结构，后续功能可以围绕既定目录继续扩展。
- 验证：仓库根目录已存在 runtime state assets tools launcher tests scripts 等核心结构，version.json 已可描述开发版版本信息。
- 下一步：继续搭建启动器应用编排、配置存储与视图模型。

## 2026-04-07 / Step 02｜完成桌面启动器分层与高级感 UI 基线
- 目标：完成桌面启动器分层与高级感 UI 基线
- 动作：实现 OpenClawLauncherApplication、PortablePaths、LauncherConfigStore、LauncherController、首次向导、主控制台以及自定义主题控件。
- 结果：Phase 1 已具备可运行的桌面壳层，用户可以完成首次配置并查看运行状态。
- 验证：main.py 可启动应用；UI 层、服务层、运行时适配层已经分离，主面板与向导均已接线。
- 下一步：接入 Node mock runtime 和 Provider 模板，建立真实运行时替换边界。

## 2026-04-07 / Step 03｜接入 Node mock runtime、自动端口处理与基础验证
- 目标：接入 Node mock runtime、自动端口处理与基础验证
- 动作：实现 MockRuntimeAdapter、健康检查、日志输出、端口冲突处理与 Provider JSON 模板，并补充单元测试和打包烟雾验证。
- 结果：开发版 MVP 可以启动本地 mock runtime，支持启动、停止、重启、健康检查和打开 WebUI。
- 验证：此前已通过 python -m unittest discover -s tests 与 PyInstaller onedir 打包烟雾验证，mock runtime 在开发版中可稳定响应。
- 下一步：补齐诊断与重置等收尾能力，并为真实 OpenClaw runtime 接入做准备。

## 2026-04-07 / Step 04｜建立 context-first 工程操作系统并回填当前项目上下文
- 目标：建立 context-first 工程操作系统并回填当前项目上下文
- 动作：创建 project-context-os Skill，初始化 OpenClaw 根目录 .context，补写总体计划、当前状态、任务拆解、决策记录和风险台账。
- 结果：OpenClaw 从零散文档推进切换为可持续维护的上下文驱动工作流。
- 验证：根目录 .context 已生成完整必需文件集合，当前状态与总体计划已去除模板占位内容。
- 下一步：继续在后续实施中按步骤追加工作日志、Bug 根因和关键决策，并在进入 Phase 2 前保持文档同步。

## 2026-04-07 / Step 05｜校验根目录 .context 并完成本轮状态收口
- 目标：校验根目录 .context 并完成本轮状态收口
- 动作：运行 project-context-os 的 validate_context.py，检查模板占位、必需文件和当前状态字段，并准备刷新 current-status。
- 结果：OpenClaw 根目录 .context 校验通过，仓库已具备后续 context-first 推进条件。
- 验证：validate_context.py 返回 context is valid；git status 仅显示 .context 新增内容。
- 下一步：把当前活跃工作切换到 Phase 1 收尾与真实 OpenClaw runtime adapter 预研。

## 2026-04-07 / Step 06｜发布 project-context-os 并解除 GitHub CLI 远程发布阻塞
- 目标：发布 project-context-os 并解除 GitHub CLI 远程发布阻塞
- 动作：引导修复 gh 登录问题，改用具备 repo 与 read:org 范围的 token 建立 CLI 登录，随后创建公开仓库并 push 本地代码。
- 结果：project-context-os 已发布到 GitHub，后续可以作为独立开源 Skill 复用，远程发布链路恢复可用。
- 验证：gh repo create 已返回 https://github.com/Antonio-bamao/project-context-os ，main 分支已成功推送并建立 origin 跟踪。
- 下一步：清理这次临时 worktree，随后把 OpenClaw 后续实施完全切换到根目录 .context 驱动。

## 2026-04-07 / Step 07｜清理 project-context-os 发布过程中的临时隔离工作区
- 目标：清理 project-context-os 发布过程中的临时隔离工作区
- 动作：删除 OpenClaw 仓库内的 .worktrees/context-os worktree、移除 feature/context-os-system 临时分支，并清空残留的 .worktrees 空目录。
- 结果：发布期间使用的项目内隐藏隔离目录已经清理，OpenClaw 仓库恢复为单工作区状态。
- 验证：git worktree list 仅保留主工作区；.worktrees 目录已不存在。
- 下一步：后续直接在主工作区继续按 .context 驱动推进 Phase 1 收尾与 Phase 2 真实 runtime 适配。

## 2026-04-08 / Phase 2 Step 01｜确认 Phase 2 默认运行时路线并落设计计划
- 目标：确认 Phase 2 默认运行时路线并落设计计划
- 动作：结合原始产品文档与 OpenClaw 官方文档，确认 U 盘版默认采用原生 Windows + Node 24 + OpenClaw v2026.4.8，WSL2 仅作为高级 fallback；新增 Phase 2 runtime adapter 设计与实施计划。
- 结果：Phase 2 进入可执行设计阶段，后续可以按 TDD 先写 adapter 测试，再实现 OpenClawRuntimeAdapter。
- 验证：.context/phase-2-runtime-adapter-design.md 与 .context/phase-2-implementation-plan.md 已创建，current-status、task-breakdown、master-plan、decisions 已同步更新。
- 下一步：新增真实 runtime adapter 的失败测试，覆盖路径、Node 解析、环境变量、日志路径和 webui_url 行为。

## 2026-04-08 / Phase 2 Step 02｜用 TDD 建立真实 OpenClawRuntimeAdapter 最小骨架
- 目标：用 TDD 建立真实 OpenClawRuntimeAdapter 最小骨架
- 动作：先新增 tests/test_openclaw_runtime_adapter.py 并确认 RED，再实现 launcher/runtime/openclaw_runtime.py 的最小 adapter，覆盖缺失 runtime、内置 Node 优先、环境变量合并、日志路径和 webui_url 行为。
- 结果：真实 runtime adapter 的基础边界已经建立，但默认运行时仍保持 mock，未影响 Phase 1 可运行性。
- 验证：python -m unittest tests.test_openclaw_runtime_adapter 通过 4 个测试；python -m unittest discover -s tests 通过 21 个测试。
- 下一步：进入 Phase 2 Step 3，增加 runtime mode 选择策略，让开发态可以在 mock 与 openclaw adapter 之间切换。

## 2026-04-08 / Phase 2 Step 03｜增加 runtime mode 选择策略
- 目标：增加 runtime mode 选择策略
- 动作：先新增 LauncherController 的 runtime_mode 失败测试，再实现 mock/openclaw adapter 选择逻辑，默认仍保持 mock。
- 结果：开发态可以通过 LauncherController(runtime_mode=openclaw) 选择真实 adapter，同时默认行为不变。
- 验证：python -m unittest tests.test_launcher_controller 通过 5 个测试；python -m unittest discover -s tests 通过 24 个测试。
- 下一步：核实并拉取 OpenClaw v2026.4.8 上游快照到 runtime/openclaw/，确认真实启动命令、健康检查入口和环境变量映射。

## 2026-04-08 / Phase 2 Step 04｜接入 OpenClaw v2026.4.8 npm runtime 并完成真实 adapter 烟雾验证
- 目标：接入 OpenClaw v2026.4.8 npm runtime 并完成真实 adapter 烟雾验证
- 动作：验证 GitHub release zip 与 npm 包差异，下载 openclaw@2026.4.8 npm 构建包，安装生产依赖，确认 gateway run 命令、OPENCLAW_STATE_DIR/CONFIG_PATH/HOME 路径策略、控制 UI 派生端口，并调整 OpenClawRuntimeAdapter。
- 结果：真实 OpenClaw gateway 可由 adapter 启动，健康检查通过，WebUI URL 指向 control UI 端口；默认 runtime 仍保持 mock，不破坏 Phase 1。
- 验证：node runtime/openclaw/openclaw.mjs --help 通过；gateway 长轮询烟雾显示 ready；OpenClawRuntimeAdapter 烟雾测试返回 RuntimeStatus(state=running, port=19884) 与 RuntimeHealth(ok=True)；python -m unittest discover -s tests 通过 24 个测试。
- 下一步：处理 runtime/openclaw 的交付体积、node_modules 纳入打包策略、内置 Node 24 下载与 PyInstaller onedir runtime 打包验证。

## 2026-04-08 / Phase 2 Step 05｜收口真实 OpenClaw runtime 产物策略与准备脚本
- 目标：收口真实 OpenClaw runtime 产物策略与准备脚本
- 动作：将 runtime/openclaw/ 标记为构建产物不进 git，新增 scripts/prepare-openclaw-runtime.ps1 负责从 npm 拉取 openclaw@2026.4.8、展开构建包、安装生产依赖并验证入口；调整 PyInstaller 打包脚本在缺少真实 runtime 时给出明确错误；补充 openclaw 模式下主面板运行时文案测试与实现。
- 结果：源码仓库保持轻量，真实 runtime 继续保留在本地作为 U 盘打包产物；后续可通过准备脚本重建 runtime/openclaw/，控制器在 openclaw 模式下会显示真实 OpenClaw gateway 状态。
- 验证：prepare-openclaw-runtime.ps1 在已有 runtime/openclaw 时拒绝覆盖；git status --ignored --short runtime/openclaw 返回 ignored；node runtime/openclaw/openclaw.mjs --version 返回 OpenClaw 2026.4.8；python -m unittest discover -s tests 通过 25 个测试。
- 下一步：准备 runtime/node/ 内置 Node 24，并做 PyInstaller onedir + 真实 OpenClaw runtime 的便携包烟雾验证。

## 2026-04-08 / Phase 2 Step 06｜准备内置 Node 24 并验证真实 OpenClaw onedir 便携包
- 目标：准备内置 Node 24 并验证真实 OpenClaw onedir 便携包
- 动作：新增 scripts/prepare-node-runtime.ps1，将本机 Node 24 复制到 runtime/node/node.exe；将 runtime/node 二进制标记为构建产物；调整 build-launcher.ps1 要求内置 Node 与 OpenClaw runtime 同时存在，并用 robocopy 复制深层 runtime 目录。
- 结果：dist/OpenClaw-Portable 已能携带 OpenClawLauncher.exe、runtime/node/node.exe 与 runtime/openclaw/；真实 gateway 可从 dist 根目录以便携路径启动。
- 验证：runtime/node/node.exe --version 返回 v24.14.1；build-launcher.ps1 构建成功；dist/OpenClaw-Portable/runtime/node/node.exe 调用 OpenClaw 返回 OpenClaw 2026.4.8；dist adapter 烟雾返回 RuntimeStatus(state=running, port=19940) 与 RuntimeHealth(ok=True)。
- 下一步：补充启动器 UI 的 runtime_mode 切换入口或开发配置开关，并继续评估真实 OpenClaw 运行时的瘦身、杀软误报和首次启动耗时。

## 2026-04-08 / Phase 2 Step 07｜补齐真实运行时自动选择入口并完成重复构建验证
- 目标：补齐真实运行时自动选择入口并完成重复构建验证
- 动作：新增 launcher/services/runtime_mode.py 的 auto/mock/openclaw 解析策略；OpenClawLauncherApplication 启动时根据便携目录完整性自动选择 runtime mode；补充 tests/test_runtime_mode.py；修复 build-launcher.ps1 重复构建时的长路径删除问题并静音 robocopy 输出。
- 结果：开发目录缺少完整 runtime 时可回退 mock，dist/OpenClaw-Portable 完整携带 runtime 时会自动选择真实 OpenClaw；重复执行 build-launcher.ps1 已可通过。
- 验证：python -m unittest discover -s tests 通过 29 个测试；build-launcher.ps1 重复构建成功；dist runtime mode 检查返回 openclaw；dist adapter 烟雾返回 RuntimeStatus(state=running, port=19960) 与 RuntimeHealth(ok=True)；validate_context.py 返回 context is valid。
- 下一步：继续处理真实 OpenClaw 首次启动耗时、运行时瘦身、杀软误报风险和 UI 对真实模式的用户提示细节。

## 2026-04-08 / Phase 2 Step 08｜收敛 VS Code 对真实 runtime 大文件树的干扰
- 目标：解决工作区中真实 OpenClaw runtime 与 dist 产物导致 IDE 显示/扫描 10 万级文件的问题。
- 动作：复核 `.context` 当前状态与任务拆解，确认真实 runtime 文件数是已知 Phase 2 阻塞项；用 git status、git ls-files 和 git check-ignore 验证 runtime/openclaw、runtime/node、dist、build、tmp 已被 `.gitignore` 命中；新增 `.vscode/settings.json`，将这些生成目录从 Explorer、搜索和文件监听中排除。
- 结果：Git 可提交视图只剩源码、测试、脚本与 `.context` 等真实改动；IDE 侧不再需要持续扫描真实 runtime 与打包产物目录。
- 验证：`.vscode/settings.json` 可被 ConvertFrom-Json 正常解析；`git ls-files --others --exclude-standard` 仅返回 17 个未跟踪条目；`git check-ignore -v` 确认 runtime/openclaw、runtime/node/node.exe、dist、build、tmp 都由 `.gitignore` 命中。
- 下一步：后续继续做真实 runtime 瘦身与 U 盘读写性能评估；本轮只处理 Git/IDE 噪声，不删除可用于便携包烟雾验证的本地构建产物。

## 2026-04-08 / Phase 2 Step 09｜收口真实运行时启动错误的用户可理解提示
- 目标：收口真实运行时启动错误的用户可理解提示
- 动作：按 TDD 新增 tests/test_runtime_errors.py，先确认缺少 runtime_errors 模块导致 RED；新增 launcher/services/runtime_errors.py，将缺少 OpenClaw runtime、启动超时、提前退出映射为中文提示；让 OpenClawLauncherApplication 的错误边界使用该映射。
- 结果：启动器弹窗不再直接暴露 package.json、healthy 等英文技术异常，真实 OpenClaw 缺运行时、首启超时和提前退出会给出可执行的中文处理建议，并指向 openclaw-runtime.err.log 供售后排查。
- 验证：python -m unittest tests.test_runtime_errors 通过 5 个测试；python -m unittest discover -s tests 通过 34 个测试。
- 下一步：继续补充真实运行时首启等待状态、Key 缺失/Provider 配置诊断和运行时瘦身评估。

## 2026-04-08 / Phase 2 Step 10｜补充真实运行时 API Key 缺失时的主面板诊断提示
- 目标：补充真实运行时 API Key 缺失时的主面板诊断提示
- 动作：按 TDD 在 tests/test_launcher_controller.py 中新增真实 openclaw 模式且 API Key 为空的视图状态测试；确认 RED 后调整 LauncherController 的 runtime message 生成逻辑，让主面板在离线状态显示 Provider 名称、API Key 缺失和重新配置建议。
- 结果：主面板在真实 OpenClaw 模式下不再用通用运行时文案掩盖空 Key 状态；用户可以直接看到当前 Provider 的 Key 未配置，并知道需要通过重新配置补充。
- 验证：python -m unittest tests.test_launcher_controller 通过 7 个测试；python -m unittest discover -s tests 通过 35 个测试。
- 下一步：继续补充真实 runtime 首启等待状态、运行时长展示，并评估 runtime/openclaw 的瘦身空间与 U 盘读写性能。

## 2026-04-09 / Phase 2 Step 11｜在主面板展示运行时长并收口 status_detail 渲染
- 目标：在主面板展示运行时长并收口 status_detail 渲染
- 动作：按 TDD 扩展 tests/test_launcher_controller.py 与 tests/test_launcher_bootstrap.py，先锁住运行中状态需要出现已运行时长、主面板需要真正渲染 status_detail；为 RuntimeStatus 增加 uptime_seconds，给 mock/openclaw adapter 记录启动后运行秒数，控制器把秒数格式化为 mm:ss 或 hh:mm:ss，并在主面板显示 status_detail。
- 结果：主面板不再只显示高层 message，运行中的 runtime 会在状态细节里展示已运行时长，界面信息更接近真实控制台。
- 验证：python -m unittest tests.test_launcher_controller tests.test_launcher_bootstrap 通过 12 个测试；python -m unittest discover -s tests 通过 36 个测试。
- 下一步：继续补充真实 runtime 首启等待状态和进一步的 Provider 配置诊断，并评估 runtime/openclaw 的瘦身空间。

## 2026-04-09 / Phase 2 Step 12｜补充真实运行时首启/重启时的等待状态提示
- 目标：补充真实运行时首启/重启时的等待状态提示
- 动作：按 TDD 为 LauncherController 新增 pending runtime view state 测试，并为 OpenClawLauncherApplication 新增启动/重启前先应用 pending 视图的顺序测试；实现 load_pending_runtime_view_state()，在 openclaw 模式下提供启动中/重启中、20-60 秒等待提示和请勿关闭窗口文案；在 app 层先刷新等待态并调用 processEvents，再执行同步 start/restart。
- 结果：用户点击启动或重启后，主面板会先切换到启动中或重启中的等待状态，不再在真实 OpenClaw 首次启动的几十秒内显得像没有响应。
- 验证：python -m unittest tests.test_launcher_controller tests.test_launcher_app 通过 10 个测试；python -m unittest discover -s tests 通过 39 个测试。
- 下一步：继续补充真实 runtime 的进一步 Provider 配置诊断，并评估 runtime/openclaw 的瘦身空间与 U 盘读写性能。

## 2026-04-09 / Phase 2 Step 13｜补充自定义 Provider 配置不完整时的主面板诊断提示
- 目标：补充自定义 Provider 配置不完整时的主面板诊断提示
- 动作：按 TDD 为 LauncherController 新增自定义 Provider 缺少 base_url/model 的视图状态与等待状态测试；扩展 make_config 测试夹具支持覆盖 Provider 字段；在 controller 中增加 Provider 配置诊断、Provider label 回退与等待态文案优先级，让缺少接口地址或模型名时明确提示重新配置。
- 结果：主面板和启动前等待态都能直接指出自定义 Provider 缺少接口地址或模型名，并把 Provider 卡片显示为“自定义 / 待补充模型”，降低用户在真实 OpenClaw 模式下看到空白模型字段时的困惑。
- 验证：python -m unittest tests.test_launcher_controller 通过 10 个测试；python -m unittest discover -s tests 通过 41 个测试。
- 下一步：进入 Phase 2 Step 7 的回归与记录：补充真实 runtime 开发态烟雾、PyInstaller onedir 烟雾与 runtime/openclaw 瘦身、U 盘读写性能评估。

## 2026-04-10 / Phase 2 Step 14｜执行 Step 7 的回归与烟雾验证
- 目标：执行 Step 7 的回归与烟雾验证
- 动作：复核 build-launcher.ps1 与本地 runtime/dist 产物，先用自定义 PortablePaths 将源码态真实 OpenClawRuntimeAdapter 的 state/logs/cache 指向 tmp 做隔离烟雾，再用同样方式验证 dist/OpenClaw-Portable/runtime；首次尝试在源码态和 dist 侧都各出现过一次 60 秒超时，于是保留日志重跑并补充成功证据；随后刷新完整单元测试。
- 结果：源码态真实 adapter 烟雾、PyInstaller onedir 构建与 dist 侧真实 adapter 烟雾均重新跑通；同时确认冷启动耗时仍存在边界波动，需要继续结合 runtime/openclaw 瘦身和超时策略评估。
- 验证：源码态 smoke 成功：elapsed_seconds=20.12, status=running, port=19884, health_ok=True；powershell -ExecutionPolicy Bypass -File .\\scripts\\build-launcher.ps1 构建成功；dist smoke 成功：elapsed_seconds=21.12, status=running, port=19940, health_ok=True；python -m unittest discover -s tests 通过 41 个测试。
- 下一步：继续评估首次冷启动的超时边界、runtime/openclaw 瘦身空间与 U 盘读写性能，并决定是否需要调整启动等待策略。

## 2026-04-10 / Phase 2 Step 15｜量化真实 OpenClaw 冷启动波动与 runtime/openclaw 体积结构
- 目标：量化真实 OpenClaw 冷启动波动与 runtime/openclaw 体积结构
- 动作：统计 runtime/openclaw 总文件数、目录体积分布和扩展名体积分布；重点确认 node_modules、dist、.ts、.map、.md 的占比；随后对源码态与 dist 侧各执行 3 轮 fresh-state 真实 OpenClawRuntimeAdapter 冷启动采样，并刷新完整单元测试。
- 结果：runtime/openclaw 当前约 0.992 GB / 93486 文件，其中 node_modules 约 0.807 GB、dist 约 0.17 GB，.ts + .map + .md 约 295 MB；fresh-state 冷启动在源码态和 dist 侧都呈现首轮 60 秒超时、后续 42/22 秒与 31/23 秒的回落模式，进一步支持冷缓存首启波动的判断。
- 验证：体积统计：runtime/openclaw=0.992 GB/93486 files；源码态 3 轮采样=[60.22 Timeout, 42.66 ok, 22.59 ok]；dist 3 轮采样=[60.25 Timeout, 31.66 ok, 23.09 ok]；python -m unittest discover -s tests 通过 41 个测试。
- 下一步：评估是否可以安全裁剪 runtime/openclaw 中的 .map/.md/.ts 等候选产物，并基于新的冷启动样本决定是否需要调整启动等待策略。

## 2026-04-10 / Phase 2 Step 16｜对便携包 dist 执行首轮安全瘦身并验证不破坏真实 runtime
- 目标：对便携包 dist 执行首轮安全瘦身并验证不破坏真实 runtime
- 动作：按 TDD 新增 runtime pruning 模块与 CLI 脚本测试，只允许默认裁剪 .map 和 .md；新增 scripts/prune-portable-runtime.py，并让 build-launcher.ps1 在复制 runtime 后自动执行；重跑 PyInstaller onedir 构建、完整单元测试，并对裁剪后的 dist 执行真实 OpenClaw adapter smoke。
- 结果：便携包构建阶段会自动从 dist/runtime/openclaw 删除 .map/.md，共移除 15743 个文件、释放 127.46 MB；裁剪后 dist/runtime/openclaw 下降到约 0.868 GB / 77743 文件，第二轮 fresh-state smoke 仍可在 27.61 秒内成功启动真实 gateway。
- 验证：python -m unittest tests.test_runtime_pruning 通过 3 个测试；python -m unittest discover -s tests 通过 44 个测试；build-launcher.ps1 成功并输出 freed_mb=127.46；裁剪后 dist smoke 先出现一次 60 秒超时、随后 27.61 秒成功，health_ok=True。
- 下一步：继续评估是否可以安全裁剪 .ts 等候选产物，并结合新的裁剪结果决定是否需要调整首轮冷启动等待策略。

## 2026-04-11 / Phase 2 Step 17｜扩展 dist 构建裁剪规则到 .d.ts 并验证收益与风险
- 目标：扩展 dist 构建裁剪规则到 .d.ts 并验证收益与风险
- 动作：先在当前 dist 产物上量化 .d.ts 与 plain .ts 的体积，确认 .d.ts 约 115.75MB、plain .ts 约 52.33MB；对当前 dist 手工删除 .d.ts 并做两轮 fresh-state smoke，观察到首轮仍超时、第二轮 27.59 秒成功；随后按 TDD 扩展 runtime pruning 默认规则到 .d.ts，重跑 build-launcher.ps1、完整单元测试与裁剪后 dist smoke。
- 结果：便携包构建阶段现在默认裁剪 .map/.md/.d.ts，共移除 40611 个文件、释放 243.21MB；裁剪后 dist/runtime/openclaw 降到约 0.754GB / 52875 文件，第二轮 fresh-state smoke 仍能在 23.09 秒成功，说明 .d.ts 裁剪未破坏真实 runtime。
- 验证：python -m unittest tests.test_runtime_pruning 通过 3 个测试；python -m unittest discover -s tests 通过 44 个测试；build-launcher.ps1 成功并输出 freed_mb=243.21；裁剪后 dist smoke 为 [61.0 Timeout, 23.09 ok]。
- 下一步：继续评估 plain .ts / .mts / .cts 等更激进候选产物，或改为基于新的冷启动样本审视 60 秒等待策略。

## 2026-04-11 / Phase 2 Step 18｜放宽真实 OpenClaw 首轮冷启动等待预算到 90 秒
- 目标：用最小改动先缓解首轮冷启动偶发撞到 60 秒阈值的问题
- 动作：按 TDD 先为 `OpenClawRuntimeAdapter` 新增默认 90 秒超时测试，并把 controller / app 的等待态测试文案改为 20-90 秒；确认 RED 后，将真实 runtime 默认 `startup_timeout_seconds` 从 60 调整为 90，并同步更新启动中的等待提示。
- 结果：产品侧不再沿用已被 fresh-state 样本证明偏紧的 60 秒默认窗口；用户在主界面会看到更贴近实际冷启动波动的 20-90 秒提示，降低首启被误判失败的概率。
- 验证：python -m unittest tests.test_openclaw_runtime_adapter tests.test_launcher_controller tests.test_launcher_app 通过 17 个测试；python -m unittest discover -s tests 通过 45 个测试；validate_context.py --project-root . 返回 context is valid。
- 下一步：继续评估 plain `.ts` / `.mts` / `.cts` 等更激进候选产物，并在 90 秒预算下补采样冷启动表现与 U 盘读写成本。

## 2026-04-11 / Phase 2 Step 19｜为更激进的 TypeScript 候选裁剪补实验性入口并做首轮验证
- 目标：验证 `plain .ts / .mts / .cts` 是否值得进入下一轮正式瘦身评估，同时不改动当前默认构建规则
- 动作：按 TDD 先为 `prune-portable-runtime.py` 新增自定义 `--pattern` 参数测试，确认 RED 后补上 CLI 能力；随后对源码态 `runtime/openclaw` 执行 `*.ts/*.mts/*.cts` dry-run，记录候选体积；再只在当前 `dist/runtime/openclaw` 上做一次实验性实删与 smoke，最后重新执行 `build-launcher.ps1` 恢复正式默认 `.map/.md/.d.ts` 裁剪结果。
- 结果：实验性模式下，源码态 `*.ts/*.mts/*.cts` 约可再释放 178.34MB；当前默认裁剪后的 dist 上实删这些候选文件后，又额外释放了 62.59MB，并且单次真实 adapter smoke 可在 21.12 秒成功。由于样本尚不足以证明稳定性，本轮只保留为正向证据，不把规则直接纳入正式构建；恢复正式默认规则后的 dist smoke 仍出现 58.49 秒冷启动，说明冷启动波动问题依然存在。
- 验证：python -m unittest tests.test_runtime_pruning 通过 4 个测试；python -m unittest discover -s tests 通过 46 个测试；python scripts/prune-portable-runtime.py --runtime-path runtime\\openclaw --dry-run --pattern *.ts --pattern *.mts --pattern *.cts 输出 freed_mb=178.34；实验性 dist 实删输出 freed_mb=62.59；实验性 dist smoke 成功，elapsed_seconds=21.12, health_ok=True；恢复正式默认规则后 build-launcher.ps1 成功，默认 dist smoke 成功，elapsed_seconds=58.49, health_ok=True；validate_context.py --project-root . 返回 context is valid。
- 下一步：继续补采样实验性 `*.ts/*.mts/*.cts` 裁剪后的 fresh-state smoke，并与默认规则基线对照，决定是否可以把更激进的裁剪规则纳入正式构建。

## 2026-04-11 / Phase 2 Step 20｜补充主界面诊断导出入口与最小可用诊断包
- 目标：提供一个不依赖命令行的售后排障入口，让用户能直接导出可用的诊断包
- 动作：按 TDD 先新增 `DiagnosticsExporter` 脱敏导出测试、主界面新增“导出诊断”按钮的 UI 烟雾测试，以及应用层导出成功提示测试；确认 RED 后新增 `launcher/services/diagnostics_export.py`，把脱敏后的配置摘要、版本信息和 `logs/*.log` 打包到 `state/backups/openclaw-diagnostics-*.zip`；随后在 `LauncherController`、`OpenClawLauncherApplication` 和主界面按钮上接线。
- 结果：主界面现在可以一键导出诊断包，里面默认包含 `manifest.json`、`config-summary.json`、`version.json` 和关键日志；诊断包不会导出原始 `.env`、明文 API Key 或明文管理密码，已经足够支撑当前阶段的售后排障。
- 验证：python -m unittest tests.test_diagnostics_export tests.test_launcher_app tests.test_launcher_bootstrap 通过 10 个测试；python -m unittest discover -s tests 通过 49 个测试；validate_context.py --project-root . 返回 context is valid。
- 下一步：继续补“恢复出厂 / 重置配置”入口，让诊断导出和重置入口一起组成更完整的售后闭环。

## 2026-04-11 / Phase 2 Step 21｜补充主界面恢复出厂入口与安全范围内的本地状态重置
- 目标：让用户无需命令行即可回到首次向导，同时避免误删 runtime、workspace 和诊断备份
- 动作：按 TDD 先新增 `FactoryResetService` 的安全范围测试、主界面新增“恢复出厂”按钮的 UI 烟雾测试，以及应用层确认后返回首次向导的测试；确认 RED 后新增 `launcher/services/factory_reset.py`，仅清空 `state/openclaw.json`、`state/.env`、provider templates、临时日志/缓存和 sessions/channels；随后在 `LauncherController`、`OpenClawLauncherApplication` 与主界面按钮上接线，并加入确认弹窗。
- 结果：主界面现在可以一键恢复到首次配置状态；当前实现会保留 `workspace/`、`state/backups/` 和 `runtime/`，因此适合作为售后排障或重新初始化入口，不会把用户工作资料和运行时本体一并抹掉。
- 验证：python -m unittest tests.test_factory_reset tests.test_launcher_app tests.test_launcher_bootstrap tests.test_launcher_controller 通过 22 个测试；python -m unittest discover -s tests 通过 53 个测试。
- 下一步：继续推进更新 / 回滚闭环，或为恢复出厂补“从备份恢复”策略。

## 2026-04-11 / Phase 2 Step 22｜补充主界面导入更新包入口与本地更新回滚闭环
- 目标：先完成不依赖联网的“本地更新包导入 + 自动备份 + 失败回滚”最小闭环，同时明确永不覆盖 `state/`
- 动作：按 TDD 先新增 `LocalUpdateImportService` 的导入成功与中途复制失败回滚测试，再为主界面新增“导入更新包”按钮的 UI 烟雾测试与应用层成功提示测试；确认 RED 后新增 `launcher/services/local_update.py`，只接管 `OpenClawLauncher.exe`、`_internal/`、`runtime/`、`assets/`、`tools/`、`README.txt` 与 `version.json` 的替换，并在更新前把旧内容备份到 `state/backups/updates/<timestamp>/`；随后在 `LauncherController`、`OpenClawLauncherApplication` 和主界面按钮上接线，失败时自动按备份还原。
- 结果：主界面现在可以手动选择新的便携包目录导入更新；更新流程会显式保留 `state/`，不会覆盖现有配置、诊断包或 workspace；复制过程中一旦失败，会把已经替换的旧内容恢复回来，先把“安全更新”这个最关键的本地闭环补齐。
- 验证：python -m unittest tests.test_local_update tests.test_launcher_app tests.test_launcher_bootstrap 通过 12 个测试；python -m unittest discover -s tests 通过 56 个测试。
- 下一步：继续补“从备份恢复旧版本”与更新包合法性校验，再考虑是否进入在线检查更新。

## 2026-04-11 / Phase 2 Step 23｜补充主界面“恢复更新备份”入口与从备份恢复旧版本闭环
- 目标：让用户无需命令行即可从 `state/backups/updates/` 选择一份历史备份恢复旧版本，同时继续保持 `state/` 永不覆盖
- 动作：先补设计规格与实现计划，明确恢复来源、恢复范围和再次备份策略；随后按 TDD 为 `RestoreUpdateBackupService` 新增恢复成功、空备份报错和中途复制失败自动回滚测试，再为 controller 补“恢复前 stop runtime 且恢复后 `_prepared=False`”测试；确认 RED 后在 `launcher/services/local_update.py` 中新增恢复服务与结果对象，在 `LauncherController`、`OpenClawLauncherApplication`、`launcher/ui/main_window.py` 上接线，并补上恢复确认弹窗、备份目录选择器与成功提示；实现过程中顺手修正了分发替换流程的回滚粒度，让“已删但尚未复制成功”的当前条目也能被自动恢复。
- 结果：主界面现在具备“恢复更新备份”入口，用户可从 `state/backups/updates/` 选一份历史备份恢复旧版本；恢复动作会先再次备份当前分发内容，再只恢复启动器本体、`_internal/`、`runtime/`、`assets/`、`tools/`、`README.txt` 与 `version.json`，不会覆盖 `state/`；一旦恢复途中失败，流程会自动把当前版本还原回来。
- 验证：docs/superpowers/specs/2026-04-11-restore-update-backup-design.md 与 docs/superpowers/plans/2026-04-11-restore-update-backup.md 已创建；python -m unittest tests.test_local_update tests.test_launcher_controller -v 通过 17 个测试；当前环境缺少 `PySide6`，因此 `tests.test_launcher_app` 与 `tests.test_launcher_bootstrap` 暂无法导入执行，待依赖具备后补跑。
- 下一步：继续补“更新包合法性校验”，并在具备 `PySide6` 的环境下补跑 UI 回归，再评估是否进入在线检查更新。

## 2026-04-11 / Phase 2 Step 24｜为“导入更新包”补严格合法性校验并收敛为升级入口
- 目标：让“导入更新包”只承担升级职责，在真正替换文件前拦住坏包、残包、同版本包和旧版本包
- 动作：先补短规格和实施计划，明确结构校验、版本规则和“小白用户默认走升级而非降级”的产品边界；随后按 TDD 为 `LocalUpdateImportService` 新增非法 JSON、缺少真实分发内容、同版本包、旧版本包和 `stable > same-dev` 的测试；确认 RED 后在 `launcher/services/local_update.py` 中补上 `version.json` 解析、分发内容存在性检查、当前/更新包版本读取，以及 `v2026.04.1-dev` / `v2026.04.1` 这类版本串的比较逻辑，并确保这些校验发生在创建备份和复制文件之前。
- 结果：现在“导入更新包”会先验证 `version.json` 合法、更新包里至少有一项真实分发内容，并要求更新包版本严格高于当前版本；同版本包会提示“无需重复导入”，旧版本包会明确引导用户改用“恢复更新备份”，从而把升级和回退两条路径真正分开。
- 验证：docs/superpowers/specs/2026-04-11-local-update-package-validation-design.md 与 docs/superpowers/plans/2026-04-11-local-update-package-validation.md 已创建；python -m unittest tests.test_local_update -v 通过 10 个测试；python -m unittest tests.test_local_update tests.test_launcher_controller -v 通过 22 个测试；python -m unittest discover -s tests 仍只因环境缺少 `PySide6` 导致 `tests.test_launcher_app`、`tests.test_launcher_bootstrap`、`tests.test_runtime_errors` 无法导入，其余 53 个测试中的非 UI 相关部分通过。
- 下一步：评估“在线检查更新”或“更新包哈希/签名校验”作为下一层更新可信度能力，并在具备 `PySide6` 的环境下补跑 UI 回归。

## 2026-04-11 / Phase 2 Step 25｜为本地更新包补 `update-manifest.json` 离线哈希校验
- 目标：让手动导入的更新包在真正替换文件前完成离线完整性校验，拦住坏包、残包和被篡改的包
- 动作：先补短规格和实施计划，明确 `update-manifest.json` 的格式、关键条目范围和目录摘要算法；随后按 TDD 新增 `tests/test_update_manifest.py` 覆盖文件/目录哈希稳定性、manifest 生成和写盘行为，并在 `tests/test_local_update.py` 中新增“缺少 manifest、manifest 版本不一致、条目记录缺失、哈希不匹配”测试；确认 RED 后新增 `launcher/services/update_manifest.py` 作为共享模块，实现关键分发内容的 `SHA-256` 文件/目录哈希、manifest 生成、写盘与校验；再新增 `scripts/generate-update-manifest.py`，并让 `scripts/build-launcher.ps1` 在复制和裁剪完成后自动为 `dist/OpenClaw-Portable` 生成 manifest；最后在 `LocalUpdateImportService` 中把 manifest 校验接到版本校验之后、备份和替换之前。
- 结果：便携包构建产物现在会自动生成 `update-manifest.json`；本地导入更新包时，除了已有的版本和结构校验外，还会强制校验 manifest 存在性、`packageVersion` 与 `version.json` 一致性，以及 `OpenClawLauncher.exe`、`runtime`、`_internal`、`assets`、`tools`、`README.txt`、`version.json` 等关键条目的 `SHA-256`。任何关键条目缺失、manifest 缺失或哈希不匹配，都会在创建备份和替换文件前被拦住。
- 验证：docs/superpowers/specs/2026-04-11-update-manifest-hash-validation-design.md 与 docs/superpowers/plans/2026-04-11-update-manifest-hash-validation.md 已创建；python -m unittest tests.test_update_manifest tests.test_local_update -v 通过 17 个测试；python -m unittest tests.test_update_manifest tests.test_local_update tests.test_launcher_controller -v 通过 29 个测试；python -m unittest discover -s tests 仍只因环境缺少 `PySide6` 导致 `tests.test_launcher_app`、`tests.test_launcher_bootstrap`、`tests.test_runtime_errors` 无法导入，其余 60 个测试中的非 UI 相关部分通过。
- 下一步：评估“在线检查更新”或“数字签名”作为下一层更新可信度能力，并在具备 `PySide6` 的环境下补跑 UI 回归。

## 2026-04-11 / Phase 2 Step 26｜补充“检查更新”在线主链路并复用既有本地导入更新安全链路
- 目标：让用户可以直接从主界面联网发现新版本、下载 zip 到临时目录，并在不重写更新内核的前提下完成本地导入更新
- 动作：先按 brainstorming 写在线更新设计 spec，再按 writing-plans 落实施计划；随后按 TDD 新增 `tests/test_online_update.py` 覆盖“有更新 / 无更新 / 更新信息非法 / 下载并解压成功 / 坏 zip 失败”，再为 controller 补“读取当前版本”和“下载后交给本地导入更新并重置 `_prepared`”测试；确认 RED 后新增 `launcher/services/online_update.py`，用固定静态 JSON 地址获取 `version`、`notes`、`packageUrl`，并用标准库 `urllib + zipfile` 把 zip 下载到 `%TEMP%\OpenClawPortable\updates\downloads\`、解压到 `%TEMP%\OpenClawPortable\updates\packages\`，再定位可导入的便携包根目录；随后在 `LauncherController` 中新增在线检查和下载导入方法，在 `launcher/app.py` 与 `launcher/ui/main_window.py` 上接入“检查更新”按钮、确认弹窗和成功提示；最后为 app/bootstrap 补上未来可运行的 UI 测试预期，等待 `PySide6` 依赖具备后补跑。
- 结果：项目现在已经具备“检查更新 -> 读取静态 `update.json` -> 用户确认 -> 下载 zip -> 解压为临时包目录 -> 交给现有本地导入更新链路”的在线更新主链路；联网部分只负责“发现和准备本地包目录”，真正的版本校验、manifest 校验、备份、替换和回滚仍由现有本地导入链路兜底。
- 验证：docs/superpowers/specs/2026-04-11-online-update-check-design.md 与 docs/superpowers/plans/2026-04-11-online-update-check.md 已创建；python -m unittest tests.test_online_update tests.test_launcher_controller -v 通过 20 个测试；python -m unittest tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v 通过 37 个测试；python -m unittest discover -s tests 仍只因环境缺少 `PySide6` 导致 `tests.test_launcher_app`、`tests.test_launcher_bootstrap`、`tests.test_runtime_errors` 无法导入，其余 68 个测试中的非 UI 相关部分通过。
- 下一步：补真实静态更新源地址和更新 JSON 发布流程，或继续推进数字签名；待具备 `PySide6` 依赖后补跑 UI 回归。
