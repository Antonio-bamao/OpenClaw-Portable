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
