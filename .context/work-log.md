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

## 2026-04-11 / Phase 2 Step 27｜补充真实更新源接入配置并集中解析 feed URL
- 目标：让正式便携包具备固定更新源，同时保留本地联调、灰度验证和售后切换更新源时的低成本覆盖能力，避免在线更新 URL 散落在多个模块里。
- 动作：先按 brainstorming 明确“内置默认地址 + 环境变量覆盖”的策略，再按 writing-plans 写实施计划；随后按 TDD 新增 `tests/test_update_feed.py`，补 `tests/test_online_update.py` 中“未显式传入地址时读取解析结果”的测试；确认 RED 后新增 `launcher/services/update_feed.py`，集中定义默认 feed 地址、环境变量名 `OPENCLAW_PORTABLE_UPDATE_FEED_URL` 和解析函数，并让 `OnlineUpdateService` 改为通过该解析层取值，顺手修正了显式默认参数会吞掉环境变量覆盖的问题。
- 结果：在线更新源地址现在已经收敛到单一模块，解析优先级固定为“显式传入 URL -> `OPENCLAW_PORTABLE_UPDATE_FEED_URL` -> 内置默认地址”；正式发布包可以直接依赖默认地址，本地测试和灰度联调则可以只改环境变量，无需重新改动业务代码或重新打包。
- 验证：docs/superpowers/specs/2026-04-11-update-feed-configuration-design.md 与 docs/superpowers/plans/2026-04-11-update-feed-configuration.md 已创建；python -m unittest tests.test_update_feed tests.test_online_update -v 通过 11 个测试；python -m unittest tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v 通过 42 个测试；python -m unittest discover -s tests 仍只因环境缺少 `PySide6` 导致 `tests.test_launcher_app`、`tests.test_launcher_bootstrap`、`tests.test_runtime_errors` 无法导入，其余 73 个测试中的非 UI 相关部分通过；validate_context.py --project-root . 返回 `context is valid`。
- 下一步：把内置默认地址替换为真实静态更新源的正式 URL，并补齐对应的 `update.json` 发布流程；如果要继续提升发布者身份可信度，则下一层进入数字签名。

## 2026-04-11 / Phase 2 Step 28｜接入 GitHub Releases 作为默认更新包托管并生成发布资产
- 目标：让便携版在不自建服务器的前提下具备可落地的发布侧更新流程，能够为当前仓库自动生成 GitHub Release 可上传的 zip 与 `update.json`，并把应用默认更新源切到当前仓库 latest release 资产地址。
- 动作：先按 brainstorming 收敛“GitHub Releases 只托管自家便携版，不直接吃 OpenClaw 上游 release”的边界，再写短 spec 与 plan；随后按 TDD 在 `tests/test_update_feed.py` 中补默认 feed 指向当前仓库 `releases/latest/download/update.json` 的断言，并新增 `tests/test_release_assets.py` 覆盖 zip 文件名、GitHub Releases `packageUrl`、`update.json` 文档内容以及最小包目录发布资产生成；确认 RED 后新增 `launcher/services/release_assets.py`，集中实现 release 资产命名、latest/download feed URL、release tag 资产 URL、zip 打包和 `update.json` 写出；再新增 `scripts/build-release-assets.py` 与 `scripts/build-release-assets.ps1` 作为发布侧编排入口，最后把 `launcher/services/update_feed.py` 的默认地址改为当前仓库的 latest release `update.json` 下载链接。
- 结果：项目现在已经具备一条最小可用的 GitHub Releases 发布路径：发布侧可以从 `dist/OpenClaw-Portable/` 自动产出 `dist/release/OpenClaw-Portable-<version>.zip` 与 `dist/release/update.json`，运行时默认会从 `https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json` 检查更新；更新包仍然是自家便携版格式，不会误把 OpenClaw 上游官方 release 当成可直接导入的更新包。
- 验证：docs/superpowers/specs/2026-04-11-github-releases-update-publishing-design.md 与 docs/superpowers/plans/2026-04-11-github-releases-update-publishing.md 已创建；python -m unittest tests.test_update_feed tests.test_release_assets -v 通过 8 个测试；更大范围回归与 context 校验待本轮收尾时继续执行。
- 下一步：运行完整可用回归，随后补充“如何把生成资产上传到 GitHub Release”的维护说明；若要继续提升可信度，则下一层进入数字签名。

## 2026-04-11 / Phase 2 Step 29｜补更新包 Ed25519 数字签名并在导入前强制验签
- 目标：在现有版本校验、manifest 校验和 GitHub Releases 托管基础上，再补一层“发布者身份可信度”，让更新导入在任何文件替换前就能拒绝未签名或伪造的更新包。
- 动作：先确认仓库已有 `requirements.txt`，再安装轻量依赖 `PyNaCl`；随后按 brainstorming 写签名 spec 与 plan，按 TDD 新增 `tests/test_update_signature.py` 以及重写 `tests/test_local_update.py`，补上“生成 keypair、签名 / 验签 round-trip、缺少签名、签名与 manifest 不匹配”的测试；确认 RED 后新增 `launcher/services/update_signature.py`，集中实现 Ed25519 keypair、`update-signature.json` 生成与验证；再重写 `launcher/services/local_update.py`，让导入链路支持注入公钥并在 manifest 校验前强制验签；最后补充 `scripts/generate-update-signing-keypair.py`、`scripts/sign-update-manifest.py`、`scripts/build-release-assets.ps1` 中的签名步骤，并把 `.local/` 加入 `.gitignore`。实现过程中还修正了多个 `scripts/*.py` 直跑时拿不到仓库根路径的问题，为这些脚本统一补上了 `sys.path` 根目录注入。
- 结果：项目现在已经具备完整的“签名构建 -> GitHub Release 资产 -> 验签导入”链路：发布侧会为 `update-manifest.json` 生成 `update-signature.json`，导入更新包时会先用仓库内置公钥验证签名，签名通过后才继续 manifest 校验和替换流程；默认私钥路径已经建立在本地忽略目录 `.local/update-signing-private-key.txt`，不会进入版本库。
- 验证：docs/superpowers/specs/2026-04-11-update-package-signature-design.md 与 docs/superpowers/plans/2026-04-11-update-package-signature.md 已创建；python -m unittest tests.test_update_signature tests.test_local_update tests.test_release_assets -v 通过 25 个测试；python -m unittest tests.test_update_signature tests.test_release_assets tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v 通过 54 个测试；python -m unittest discover -s tests 仍只因环境缺少 `PySide6` 导致 `tests.test_launcher_app`、`tests.test_launcher_bootstrap`、`tests.test_runtime_errors` 无法导入，其余 82 个测试中的非 UI 相关部分通过；python scripts/generate-update-signing-keypair.py --private-key-path .local/tmp-signing-key.txt 成功后已删除测试用临时私钥；validate_context.py --project-root . 返回 `context is valid`。
- 下一步：补“如何备份 `.local/update-signing-private-key.txt`、如何在新机器上恢复、以及如何轮换公钥 / keyId”的维护说明；待具备 `PySide6` 依赖后补跑 UI 回归。

## 2026-04-11 / Phase 2 Step 30 - Add update signing key rotation support

- Goal: Allow update signing keys to rotate safely by supporting multiple trusted Ed25519 public keys keyed by `keyId`.
- Actions: Added a short spec and implementation plan for key rotation, wrote failing tests for secondary trusted keys in `tests/test_update_signature.py` and `tests/test_local_update.py`, then extended `launcher/services/update_signature.py` and `launcher/services/local_update.py` so signature verification can select the correct public key from a trusted map.
- Result: `update-signature.json` format stays stable, while `LocalUpdateImportService` can now accept `signature_public_keys={keyId: publicKey}`. Packages signed by an explicitly trusted secondary key can import successfully; packages signed with an unknown `keyId` fail before manifest validation or file replacement.
- Verification: `python -m unittest tests.test_update_signature tests.test_local_update -v` passed 24 tests. `python -m unittest tests.test_update_signature tests.test_release_assets tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v` passed 57 tests. `python -m unittest discover -s tests` still only fails on the existing missing `PySide6` imports in `tests.test_launcher_app`, `tests.test_launcher_bootstrap`, and `tests.test_runtime_errors`. `validate_context.py --project-root .` returned `context is valid`.

## 2026-04-11 / Phase 2 Step 31｜补发布维护手册

- 目标：补齐 GitHub Release 资产上传、签名私钥备份/恢复与 keyId 轮换的发布维护说明。
- 动作：新增 `docs/release-maintenance-playbook.md`，整理发版前检查、`build-release-assets.ps1` 产物生成、GitHub Release 上传、私钥备份/恢复、keyId 轮换、回归验证与故障处理；同步刷新 `.context/current-status.md` 与 `.context/task-breakdown.md`。尝试使用 `append_work_log.py` 追加日志时，Windows 对 `.context/work-log.md` 返回 `PermissionError`，因此改用同结构直接补记。
- 结果：发布维护操作不再散落在多个设计 spec 中，维护者可以按 runbook 完成 release 资产生成、上传、私钥恢复与轮换操作。
- 验证：已人工检查 `docs/release-maintenance-playbook.md` 的路径、命令、keyId 与发布资产命名；`python -m unittest tests.test_update_signature tests.test_release_assets -v` 通过 11 个测试；`validate_context.py --project-root .` 返回 `context is valid`。
- 下一步：可做真实 GitHub Release 上传演练，或转回 runtime 瘦身 / U 盘性能评估。

## 2026-04-12 / Phase 2 Step 32｜完成 `v2026.04.2` latest release 演练

- 目标：完成 GitHub latest release 真实发版演练，并验证匿名 `update.json` 与 zip 下载链路。
- 动作：将 `version.json` 切到 `v2026.04.2`；准备 `runtime/openclaw` 与 `runtime/node`；安装 `PySide6` / `PyInstaller`；构建 `dist/release` 资产；验证 zip 结构、签名、manifest 与 dist 真实 runtime smoke；提交并推送 `main`；创建并推送 `v2026.04.2` tag；用户在 GitHub Release 上传 zip 与 `update.json`；仓库由 private 改为 public 后重新验证 `latest/download/update.json` 与 zip HEAD。
- 结果：GitHub Releases latest 更新入口已可匿名访问，`OnlineUpdateService` 可发现 `v2026.04.2`，zip 资产 HEAD 返回 200 且 `Content-Length` 与本地包一致。
- 验证：`python -m unittest discover -s tests` 通过 103 个测试；dist 真实 runtime smoke 成功 `elapsed_seconds=37.01`、`health_ok=True`；latest `update.json` 返回 200 且 `version=v2026.04.2`；`OnlineUpdateService.check_for_updates("v2026.04.1")` 返回 `update_available=True`；zip HEAD 返回 200、`Content-Length=212380004`。
- 下一步：继续验证启动器 GUI 的“检查更新”入口，或转回 runtime 瘦身、U 盘读写性能与商业交付文档。

## 2026-04-12 / Phase 2 Step 33｜修复启动器按钮慢响应与重复点击卡死风险

- 目标：修复真实 runtime 和在线更新链路下，按钮点击后 UI 主线程被长耗时动作阻塞、多次点击容易让 Windows 标记为“未响应”的问题。
- 动作：按 TDD 先补 `tests/test_launcher_app.py` 的重复点击保护测试，以及 `tests/test_launcher_bootstrap.py` 的按钮 busy 态 UI 测试；随后在 `OpenClawLauncherApplication` 中加入单线程后台执行器和 Qt signal 回到 UI 线程的完成回调，把启动、停止、重启、导入更新包、检查更新、下载导入更新和恢复更新备份改为后台执行；同时在主窗口为运行时按钮、检查更新、导入更新包、恢复更新备份增加禁用与“正在...”文案。
- 结果：慢操作不再直接堵住 PySide 主线程；同一动作在进行中会被按钮禁用和应用层 busy 集合双重拦截，避免用户多点几下把多个网络下载、启动 runtime 或导入更新任务堆进事件队列。
- 验证：`python -m unittest tests.test_launcher_app tests.test_launcher_bootstrap -v` 通过 17 个测试；`python -m unittest discover -s tests` 通过 107 个测试。
- 下一步：若要让已发布的 `v2026.04.2` 用户拿到该修复，需要准备 `v2026.04.3` 热修复 release，重新构建并上传 zip 与 `update.json`。

## 2026-04-12 / Phase 2 Step 34｜新增便携交付包只读审计工具

- 目标：在暂不更新 release 的前提下，先量化当前交付包大小、文件数、主要体积分布、必需文件缺失和 U 盘写入风险，为后续瘦身与交付体验优化提供证据。
- 动作：补 `docs/superpowers/specs/2026-04-12-portable-package-audit-design.md` 与 `docs/superpowers/plans/2026-04-12-portable-package-audit.md`；按 TDD 新增 `tests/test_portable_audit.py`，先验证服务不存在的 RED，再实现 `launcher/services/portable_audit.py` 与 `scripts/audit-portable-package.py`；运行真实 `dist/OpenClaw-Portable` 审计时发现 `node_modules/**/cache` 被误报为写入风险，补回归测试后把风险判断收紧到包根、`state/` 或 `runtime/` 下的非 `node_modules` 写入目录。
- 结果：现在可以运行 `python scripts/audit-portable-package.py --top 8` 得到 JSON 报告；当前 dist 包约 `582.17MB`、`31221` 个文件，最大目录为 `runtime` `471.09MB`、`runtime/openclaw` `383.90MB`、`runtime/openclaw/node_modules` `237.63MB`、`runtime/openclaw/dist` `135.49MB`；必需路径齐全；写入风险只剩 `state/logs`。
- 验证：`python -m unittest tests.test_portable_audit -v` 通过 3 个测试；`python -m unittest discover -s tests` 通过 110 个测试；`python scripts/audit-portable-package.py --top 8` 成功输出审计报告。
- 下一步：处理 `state/logs` 是否应排除在发布包之外，随后再根据审计数据决定是否继续安全裁剪 runtime 或转向商业交付文档。

## 2026-04-12 / Phase 2 Step 35｜拦截 smoke 后 dist 的运行态 state 进入 release zip

- 目标：修复交付审计发现的 `dist/OpenClaw-Portable/state/logs` 等运行态残留风险，防止开发者把已经真实运行过的 dist 目录直接重新打成发布 zip。
- 动作：先定位根因：`scripts/build-launcher.ps1` 只复制 `state/provider-templates`，当前 dist 中的 `openclaw.json`、`logs`、`tasks`、`workspace` 等来自真实 runtime smoke 对 dist 的运行写入；本地已发布的 `dist/release/OpenClaw-Portable-v2026.04.2.zip` 经检查只包含 `state/provider-templates` 四个模板文件，没有包含运行态 state。随后按 TDD 为审计报告新增 `unexpected_state_paths` 测试，并为 `build_release_assets()` 新增“存在 mutable state entries 时拒绝打包”的测试；确认 RED 后在 `portable_audit.py` 中新增 release state 清洁策略，只允许 `state/provider-templates`，并让 `release_assets.py` 在创建 zip 前调用该策略；最后更新发布维护手册，提醒发布时重新运行 `build-release-assets.ps1` 从干净 dist 生成资产，不要拿 smoke 过的 dist 手动打包。
- 结果：审计报告现在能列出 `state/backups`、`state/canvas`、`state/channels`、`state/logs`、`state/openclaw.json`、`state/sessions`、`state/tasks`、`state/workspace` 这类不可发布运行态条目；`python scripts/build-release-assets.py --package-root dist\OpenClaw-Portable ...` 在当前 smoke 过的 dist 上会明确失败并列出这些路径，避免污染下一次 release。
- 验证：`python -m unittest tests.test_portable_audit tests.test_release_assets -v` 通过 9 个测试；`python -m unittest discover -s tests` 通过 112 个测试；真实 `v2026.04.2` 本地 zip state 检查确认仅有 provider templates；当前 smoke 过的 dist 触发 release state guard 的失败符合预期。
- 下一步：后续要生成新 release 时先运行完整 `scripts/build-release-assets.ps1` 重建干净 dist；在正式更新前可继续做 runtime 体积瘦身与 U 盘读写性能评估。

## 2026-04-12 / Phase 2 Step 36｜扩展交付审计的 runtime 裁剪候选报告

- 目标：在不删除文件、不改默认裁剪规则、不更新 release 的前提下，先量化下一层可裁剪候选，为 runtime 瘦身决策提供证据。
- 动作：补 `docs/superpowers/specs/2026-04-12-runtime-prune-candidate-audit-design.md` 与 `docs/superpowers/plans/2026-04-12-runtime-prune-candidate-audit.md`；按 TDD 扩展 `tests/test_portable_audit.py`，要求审计结果包含 `prune_candidates` 分组，并确认 `.d.ts` 只归入 type declarations、不重复归入 TypeScript sources；确认 RED 后在 `launcher/services/portable_audit.py` 中新增 `PortablePruneCandidateGroup`、低/中风险候选规则和 JSON 序列化，复用已有 file-size map，不增加第二次完整扫描。
- 结果：`python scripts/audit-portable-package.py --top 12` 现在会输出 `prune_candidates`：当前 smoke-mutated dist 中默认低风险组 `source_maps`、`markdown_docs`、`type_declarations` 都为 `0`，说明正式默认裁剪已生效；中风险候选为 `typescript_sources` 约 `22.49MB / 4961` 文件，`test_artifacts` 约 `3.88MB / 740` 文件，下一步若要继续瘦身应围绕这两组做重建与真实 runtime smoke。
- 验证：`python -m unittest tests.test_portable_audit -v` 通过 5 个测试；`python -m unittest discover -s tests` 通过 113 个测试；`python scripts/audit-portable-package.py --top 12` 成功输出候选分组和真实体积分布。
- 下一步：如继续瘦身，优先用实验性 `--pattern *.ts --pattern *.mts --pattern *.cts` 和测试产物 pattern 在干净 dist 上 dry-run/裁剪，然后执行真实 runtime smoke；通过多轮证据后再考虑进入默认 prune。

## 2026-04-12 / Phase 2 Step 37 - Add real portable runtime stability verification

- Goal: add a repeatable verification tool that measures real cold-start and restart stability against `dist/OpenClaw-Portable` without polluting package-root `state/`.
- Actions: wrote the spec and plan, then followed TDD to add `tests/test_runtime_stability.py`, `launcher/services/runtime_stability.py`, and `scripts/verify-portable-runtime-stability.py`; reproduced the first real failure, traced it to launcher-schema config being written into isolated `state/openclaw.json`, and fixed the runner so it preserves package runtime config (`state/openclaw.json` / `.env`) while preparing the runtime adapter directly.
- Result: the verifier now creates isolated roots under `%TEMP%\\OpenClawPortableVerification\\<run>\\...`, records per-run elapsed time plus stdout/stderr log paths, and emits a JSON report suitable for release gating or postmortem review.
- Verification: `python -m unittest tests.test_runtime_stability -v` passed 7 tests; `python -m unittest discover -s tests` passed 120 tests; `python .\\scripts\\verify-portable-runtime-stability.py --package-root dist\\OpenClaw-Portable --cold-runs 3 --restart-runs 2 --output tmp\\runtime-stability-report.json` passed all 5 runs with cold starts at `27.61s`, `25.59s`, `28.62s`, restarts at `27.61s`, `25.62s`, max `28.62s`, avg `27.01s`; `python .\\scripts\\audit-portable-package.py --top 5` confirmed no new verifier-caused package pollution beyond the previously known smoke-mutated state entries.
- Next: keep this verifier in the release checklist, finish the remaining stability-first delivery items, and only rebuild/publish a new clean release after the full delivery set is ready.

## 2026-04-12 / Phase 2 Step 38｜完成 clean dist 的 TypeScript / test artifacts 联合裁剪实验

- 目标：把 `typescript_sources` 与 `test_artifacts` 两组中风险候选真正落到 clean dist 实验包上，验证实验入口、裁剪口径和真实 runtime 稳定性是否能闭环。
- 动作：先重建干净 `dist/OpenClaw-Portable`，并用 `python .\\scripts\\audit-portable-package.py --package-root dist\\OpenClaw-Portable --top 8` 确认 `unexpected_state_paths` 与 `write_risk_directories` 均为 `[]`；随后发现 `scripts/prune-portable-runtime.py` 的 `--pattern` 只能覆盖 `test_artifacts` 中的 `338` 个 `*.test.* / *.spec.*` 文件，而审计口径还包含 `__tests__/test` 目录下的文件，总计应为 `740` 个，因此按 TDD 扩展 `tests/test_runtime_pruning.py`、`launcher/services/runtime_pruning.py` 与 `scripts/prune-portable-runtime.py`，新增实验性 `--directory-name` 支持；最后在 `tmp/prune-experiments/ts-and-tests/` 上联合裁剪 `*.ts/*.mts/*.cts/*.test.*/*.spec.*` 与 `__tests__/test` 目录内容，并执行真实稳定性验证。
- 结果：runtime prune 实验入口现在可以和审计口径保持一致；联合裁剪实验共删除 `5381` 个文件、释放 `24.26MB`，实验包审计中 `typescript_sources` 与 `test_artifacts` 两组均降为 `0`，且没有引入新的运行态污染或写入风险警告。
- 验证：`python -m unittest tests.test_runtime_pruning -v` 通过 6 个测试；`python .\\scripts\\prune-portable-runtime.py --runtime-path dist\\OpenClaw-Portable\\runtime\\openclaw --dry-run --pattern *.ts --pattern *.mts --pattern *.cts` 返回 `4961` 文件 / `22.49MB`，`python .\\scripts\\prune-portable-runtime.py --runtime-path dist\\OpenClaw-Portable\\runtime\\openclaw --dry-run --pattern *.test.* --pattern *.spec.* --directory-name __tests__ --directory-name test` 返回 `740` 文件 / `3.88MB`，与审计一致；`python .\\scripts\\audit-portable-package.py --package-root tmp\\prune-experiments\\ts-and-tests --top 6` 显示实验包约 `558.52MB` / `25837` 文件且 `warnings=[]`；`python .\\scripts\\verify-portable-runtime-stability.py --package-root tmp\\prune-experiments\\ts-and-tests --cold-runs 3 --restart-runs 2 --output tmp\\prune-experiments\\ts-and-tests-runtime-stability.json` 通过全部 5 轮，max `28.62s`、avg `22.50s`；`python -m unittest discover -s tests` 通过 `122` 个测试。
- 下一步：基于这轮证据决定是否把 `typescript_sources` 与 `test_artifacts` 提升为默认 prune 规则；若进入默认规则，需接入正式构建链路、重建 clean dist，并再次跑完整稳定性 gate 后再考虑下一版 release。

## 2026-04-12 / Phase 2 Step 39｜将 TypeScript sources + test artifacts 提升为默认 prune 规则

- 目标：把已经在实验包上验证通过的 `typescript_sources` 与 `test_artifacts` 真正并入默认构建裁剪路径，让正式 `build-launcher.ps1` 直接产出更轻的 clean dist。
- 动作：按 TDD 先把 `tests/test_runtime_pruning.py` 的默认行为改成要求删除 `.ts/.mts/.cts`、`*.test.*/*.spec.*` 以及 `__tests__/test` 目录后代文件；确认 RED 后，在 `launcher/services/runtime_pruning.py` 中把默认规则扩展为低风险 + 已验证中风险组合，并新增 `DEFAULT_PRUNE_DIRECTORY_NAMES`；随后在 `scripts/prune-portable-runtime.py` 中保持“无参数走默认、显式参数走实验覆盖”的语义，避免实验命令意外混入新的默认目录规则；最后重新执行 `scripts/build-launcher.ps1`，让默认构建链路直接使用新规则。
- 结果：正式默认 prune 已经覆盖 source maps、markdown、type declarations、TypeScript sources 与 test artifacts；`build-launcher.ps1` 产出的 clean `dist/OpenClaw-Portable` 现在约 `558.52MB / 25837` 文件，相比上一个 clean dist 进一步减少约 `24.26MB` 与 `5381` 个文件。
- 验证：`python -m unittest tests.test_runtime_pruning -v` 通过 6 个测试；`powershell -ExecutionPolicy Bypass -File .\\scripts\\build-launcher.ps1` 实际输出默认 prune 删除 `30904` 个文件、释放 `165.19MB`；`python .\\scripts\\audit-portable-package.py --package-root dist\\OpenClaw-Portable --top 8` 显示 `unexpected_state_paths=[]`、`write_risk_directories=[]` 且 `typescript_sources` / `test_artifacts` 候选均为 `0`；`python .\\scripts\\verify-portable-runtime-stability.py --package-root dist\\OpenClaw-Portable --cold-runs 3 --restart-runs 2 --output tmp\\runtime-stability-report-default-prune.json` 通过全部 5 轮，max `26.64s`、avg `24.77s`；`python -m unittest discover -s tests` 通过 `122` 个测试。
- 下一步：继续做 U 盘读写性能与杀软误报风险评估；若准备下一版 release，则基于这份默认 prune 后的 clean dist 继续走发布资产构建、在线更新链路复验和版本收口。

## 2026-04-12 / Phase 3 Design Step 01｜完成飞书私聊渠道 MVP 设计 spec

- 目标：把“渠道接入”从泛化愿景收窄成一个真正可落地的第一个渠道闭环，并在实现前锁定边界、状态模型、运行链路和验收标准。
- 动作：按 brainstorming 流程先结合产品架构文档与 `.context` 现状，收敛出“飞书优先、启动器优先、私聊闭环、复用 OpenClaw runtime / 插件链路”的范围；随后写成正式 spec `docs/superpowers/specs/2026-04-12-feishu-private-chat-channel-design.md`，覆盖用户操作流、`state/channels/feishu/` 配置/状态分层、启动器与 runtime 分工、错误处理、诊断脱敏与验收标准。
- 结果：渠道接入现在不再是“微信/飞书/QQ/企微一起预研”的松散任务，而是被收敛成一个可写实现计划的飞书 MVP 子项目。
- 验证：已对 spec 做自检，确认没有 `TODO` / `TBD` 占位，范围、非目标、状态机和验收标准前后一致。
- 下一步：请用户先 review `docs/superpowers/specs/2026-04-12-feishu-private-chat-channel-design.md`；如无修改，再进入实现计划编写。


## 2026-04-12 / Phase 3 Planning Step 02 - Convert Feishu spec into executable implementation plan

- Goal: turn the approved Feishu private-chat MVP spec into a task-by-task implementation plan before starting code changes.
- Actions: reviewed the existing launcher controller, config store, runtime adapter, diagnostics exporter, launcher UI shell, and bundled OpenClaw Feishu plugin metadata; then wrote docs/superpowers/plans/2026-04-12-feishu-private-chat-channel.md with explicit file ownership, TDD-first tasks, runtime projection details, diagnostics/help work, and verification commands.
- Result: the Feishu channel thread is now ready for execution as a bounded project rather than an open-ended design item.
- Verification: self-reviewed the plan against the approved spec, removed implementation placeholders, and confirmed it stays within Feishu only, launcher-first, private-chat MVP.
- Next: choose execution mode and begin Task 1 from the plan.

## 2026-04-13 / Phase 3 Implementation Step 03 - Implement Feishu private-chat channel MVP

- Goal: move the first real channel integration from spec/plan into a launcher-usable MVP rather than continuing packaging-only work.
- Actions: used an isolated worktree for the Feishu implementation; added Feishu channel paths, storage service, credential validation, runtime projection, `state/openclaw.json` merge, status refresh, launcher-facing view state, controller save/test/enable/disable APIs, main-window Feishu card, app event binding, diagnostics redaction, and `assets/guide/setup-feishu.html`. During review, fixed two important edge cases: malformed Feishu config now safely falls back instead of blocking launcher startup, and runtime config patch data is actually merged into the runtime config instead of being dead plumbing.
- Result: users can now save Feishu App ID / App Secret in the launcher, test credentials, enable or disable the private-chat channel, see status, export diagnostics without leaking the App Secret, and open an offline Feishu setup guide. The runtime side receives both env vars and `channels.feishu` config while preserving existing launcher config keys.
- Verification: `python -m unittest discover -s tests` passed `141` tests; `git diff --check` passed aside from existing line-ending warnings reported by Git on Windows.
- Remaining: a real private-chat proof requires an actual Feishu app and network access to Feishu; group chat, WeChat/QQ/WeCom, WebUI dual-entry, and a Python-side message bridge remain intentionally out of scope.


## 2026-04-13｜Complete Feishu private-chat MVP branch integration
- 目标：Complete Feishu private-chat MVP branch integration
- 动作：Pushed local main commit 8b1c473 to origin/main after confirming only main worktree remains and the working tree is clean.
- 结果：Remote main now includes the Feishu private-chat MVP implementation commit.
- 验证：git status --short --branch reports main aligned with origin/main; prior Feishu implementation verification passed python -m unittest discover -s tests with 141 tests.
- 下一步：Shift to the next unblocked delivery-risk item: U-disk read/write performance and anti-virus false-positive assessment, while real Feishu E2E remains dependent on actual credentials.

## 2026-04-13｜Collect local delivery-risk baseline evidence
- 目标：Collect local delivery-risk baseline evidence
- 动作：Ran portable package audit on dist/OpenClaw-Portable, enumerated Windows drive types, checked Defender status, scanned the launcher EXE and release zip with Windows Defender, queried Defender threat detections, and updated current-status/task-breakdown/risk-register.
- 结果：Clean dist remains 558.52MB / 25837 files with no release-state or write-risk warnings; no usable removable U-disk is mounted; Defender local custom scans completed and threat detection query returned no detections.
- 验证：audit-portable-package.py output showed required_paths_missing=[], unexpected_state_paths=[], write_risk_directories=[], prune candidates all zero; Get-CimInstance reported F: removable but no filesystem/size and G:/H: fixed; Get-MpComputerStatus showed Defender protections enabled; Get-MpThreatDetection returned no rows; validate_context.py returned context is valid.
- 下一步：Run real removable-media read/write and cold-start measurement once a usable U-disk or target delivery path is available; otherwise draft a small assessment plan/checklist for SmartScreen and multi-engine AV validation.

## 2026-04-13｜Add a delivery flow verification gate
- 目标：Add a delivery flow verification gate
- 动作：Added launcher.services.delivery_gate and scripts/verify-delivery-flow.py with TDD coverage in tests/test_delivery_gate.py; the gate reuses package audit, release asset checks, runtime stability verification, and explicit pending checks for Feishu E2E, removable media, and multi-engine AV/SmartScreen evidence.
- 结果：The new gate reports structured passed/failed/pending/skipped checks and can run against the real main-worktree dist without publishing or mutating product state. It also caught that the current dist package root needed update-signature.json; regenerated the local ignored signature artifact from .local/update-signing-private-key.txt before rerunning the gate.
- 验证：RED: tests.test_delivery_gate initially failed on missing launcher.services.delivery_gate, and later failed when release zip contents were not checked. GREEN: python -m unittest tests.test_delivery_gate -v passed 4 tests; python -m unittest discover -s tests passed 145 tests. Real gate rerun with one cold start and one restart returned status pending: audit passed, release assets passed, runtime stability passed, and only external Feishu/U-disk/multi-engine AV evidence remains pending.
- 下一步：Merge the delivery-flow-gate branch back to main, then use verify-delivery-flow.py as the release readiness command before preparing the next package/release.

## 2026-04-13｜Verify delivery flow gate after merging to main
- 目标：Verify delivery flow gate after merging to main
- 动作：Fast-forward merged delivery-flow-gate into main, reran delivery gate tests, full unittest suite, context validation, and a serial real dist delivery gate with one cold start and one restart.
- 结果：Main now includes the delivery flow gate. The real dist gate returned status=pending because external Feishu E2E, removable-media, and multi-engine AV/SmartScreen evidence are still absent; package audit, release assets, and runtime stability passed.
- 验证：python -m unittest tests.test_delivery_gate -v passed 4 tests; python -m unittest discover -s tests passed 145 tests; validate_context.py returned context is valid; python scripts\\verify-delivery-flow.py --package-root dist\\OpenClaw-Portable --release-dir dist\\release --cold-runs 1 --restart-runs 1 --timeout-seconds 90 returned status=pending with audit passed, release-assets passed, runtime-stability passed, max 22.59s, avg 21.87s.
- 下一步：Provide real Feishu app credentials, a usable U-disk or delivery media path, and multi-engine AV/SmartScreen evidence to clear the remaining external pending checks; otherwise the local code flow is ready to use the gate before the next release.
