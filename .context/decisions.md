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

## 2026-04-11｜真实 OpenClaw 首轮冷启动默认等待窗口先放宽到 90 秒

- 背景：Step 7 的 fresh-state smoke 已多次显示源码态与 dist 侧都可能在 60 秒附近撞线超时，而后续同配置重试又能在 20-40 秒内成功，说明产品默认 60 秒窗口对冷缓存首启偏紧。
- 理由：在根因尚未完全定位前，先通过更宽的默认等待窗口与更准确的等待文案降低首启误判失败的概率，属于风险更低的缓解措施；相比继续堆复杂启动逻辑，这一改动更符合当前证据。
- 影响范围：`launcher/runtime/openclaw_runtime.py` 的默认 `startup_timeout_seconds`、主界面启动等待文案、首启体验与 Step 7 后续采样口径。
- 后续约束：90 秒只是缓解，不代表问题已根治；后续仍需继续量化 plain `.ts` / `.mts` / `.cts` 裁剪空间、U 盘读写性能与 fresh-state 冷启动样本，再决定是否继续调整等待策略。

## 2026-04-11｜更激进的 `*.ts/*.mts/*.cts` 裁剪先保留为实验性入口，不进入默认构建

- 背景：在 `.map/.md/.d.ts` 默认裁剪完成后，源码态 dry-run 仍显示 `*.ts/*.mts/*.cts` 约占 178.34MB；对当前 dist 实验性实删后，还能再释放 62.59MB，并且单次 smoke 在 21.12 秒成功。
- 理由：这些候选文件已经不再是纯文档或类型声明，虽然单次 smoke 给出了正向信号，但稳定性样本仍不足；与其直接扩大默认裁剪范围，不如先给 pruning CLI 增加实验性 `--pattern` 入口，把验证与正式规则解耦。
- 影响范围：`scripts/prune-portable-runtime.py`、`tests/test_runtime_pruning.py`、后续瘦身试验流程与 Step 7 的回归采样方法。
- 后续约束：当前正式构建仍只允许默认裁剪 `.map`、`.md` 与 `.d.ts`；`*.ts/*.mts/*.cts` 只能通过实验性 `--pattern` 手工验证，直到补足多轮 fresh-state smoke 证据后再决定是否升级为默认规则。

## 2026-04-11｜诊断包默认只导出脱敏摘要与关键日志，不打包原始敏感配置

- 背景：项目已经进入真实 runtime 与售后排障阶段，用户需要一个一键导出诊断包的入口；同时 `risk-register.md` 已明确诊断包泄露敏感信息是高风险项。
- 理由：当前阶段的售后定位主要需要版本信息、运行模式、配置摘要和关键日志，并不需要原始 `.env` 或明文 API Key；先做最小可用且默认脱敏的导出，比“全量打包再人工筛查”更稳妥。
- 影响范围：`launcher/services/diagnostics_export.py`、主界面“导出诊断”入口、售后排障流程与后续诊断包格式约束。
- 后续约束：诊断包默认不得包含明文 API Key、明文管理密码或原始 `.env`；后续若要扩大导出范围，必须先补脱敏规则与回归测试。

## 2026-04-11｜恢复出厂先采用“安全重置”策略，不删除 runtime、workspace 与诊断备份

- 背景：项目需要一个非命令行的“恢复出厂 / 重置配置”入口，但便携版同时承载真实 runtime、用户工作目录和已导出的诊断包，误删代价较高。
- 理由：当前最常见的售后场景是“配置错了、状态乱了、需要重新走向导”，并不是“把整个 U 盘内容抹掉”；因此先把恢复出厂限制在启动器配置和本地临时状态上，既能解决大多数排障问题，也更符合小白用户的心理预期。
- 影响范围：`launcher/services/factory_reset.py`、`LauncherController.reset_factory_state()`、主界面“恢复出厂”入口、售后排障与重新初始化流程。
- 后续约束：恢复出厂默认只清理 `state/openclaw.json`、`state/.env`、provider templates、临时日志/缓存和 sessions/channels；不得删除 `runtime/`、`state/workspace/` 或 `state/backups/`，除非后续单独设计并测试更激进的重置模式。

## 2026-04-11｜本地导入更新包默认只替换分发内容，更新前自动备份且永不覆盖 `state/`

- 背景：当前项目需要先把“更新 / 回滚”做成可落地的本地闭环，但仓库里还没有现成的在线 updater；同时 `risk-register.md` 已明确更新失败回滚和保护用户状态目录是高优先级约束。
- 理由：先支持用户手动选择新的便携包目录导入更新，可以最小成本补上“安全替换 + 自动回滚”闭环；而把更新范围严格限制在启动器本体、`_internal/`、`runtime/`、`assets/`、`tools/`、`README.txt` 与 `version.json`，可以避免误覆盖 `state/` 下的配置、诊断包和 workspace。
- 影响范围：`launcher/services/local_update.py`、`LauncherController.import_update_package()`、主界面“导入更新包”入口、`state/backups/updates/` 备份目录结构，以及后续更新 / 回滚策略设计。
- 后续约束：本地导入更新包默认不得复制或覆盖 `state/`；更新前必须先把即将替换的旧内容备份到 `state/backups/updates/`，复制过程中任一步失败都必须自动回滚；后续如果要支持在线下载或更广的替换范围，必须先补更新包合法性校验与恢复路径测试。

## 2026-04-11｜从更新备份恢复旧版本默认继续只恢复分发内容，恢复前再次备份当前版本

- 背景：在“导入更新包 + 自动备份 + 失败回滚”闭环完成后，用户仍然缺少一个非命令行的主动恢复入口，无法从 `state/backups/updates/` 中选一份历史备份把程序恢复到旧版本。
- 理由：恢复旧版本本质上与导入更新包是同一类“替换分发内容”的动作；继续沿用只恢复 `OpenClawLauncher.exe`、`_internal/`、`runtime/`、`assets/`、`tools/`、`README.txt` 与 `version.json` 的边界，并在恢复前再次备份“当前版本”，可以同时满足小白用户的可恢复体验和便携版对 `state/` 的强保护约束。
- 影响范围：`launcher/services/local_update.py` 中的恢复服务、`LauncherController.restore_update_backup()`、主界面“恢复更新备份”入口、`state/backups/updates/` 的恢复来源与再次备份策略。
- 后续约束：从更新备份恢复旧版本默认不得覆盖 `state/`；恢复前必须再次备份当前分发内容，恢复过程中任一步失败都必须自动回滚；若后续要把恢复来源扩展到在线下载产物或跨版本迁移包，必须先补更新包合法性校验与恢复路径回归。

## 2026-04-11｜“导入更新包”默认是严格升级入口，不承担降级职责

- 背景：在本地更新导入和恢复更新备份两个入口都具备后，如果继续让“导入更新包”接受同版本或旧版本包，小白用户很容易把“升级”和“回退”两条路径混用，导致误操作和售后沟通成本升高。
- 理由：既然项目已经有专门的“恢复更新备份”入口，那么“导入更新包”就应该专门承担“升级”职责；因此更新包除了需要 `version.json` 合法、至少带一项真实分发内容外，还必须保证版本严格高于当前版本。这样既能拦住空包/残包，也能把降级统一收敛到恢复路径。
- 影响范围：`launcher/services/local_update.py` 的更新包结构校验、版本解析与比较逻辑、本地更新错误文案，以及后续在线更新策略的版本门槛。
- 后续约束：同版本包必须直接提示“无需重复导入”；旧版本包必须明确提示改用“恢复更新备份”；任何真正的降级能力都不得再走“导入更新包”入口，除非后续重新设计并记录决策。

## 2026-04-11｜本地更新包默认要求 `update-manifest.json`，以离线 `SHA-256` 校验关键分发内容完整性

- 背景：在“导入更新包”已经具备版本规则后，剩余高频风险变成“用户拿到的是不是完整包、下载或拷贝过程中有没有损坏、关键文件有没有被替换”。仅靠 `version.json` 和目录结构不足以发现这类问题。
- 理由：相比立即引入联网签名验证，先为便携包构建产物自动生成 `update-manifest.json`，并在导入更新包前离线校验关键条目的 `SHA-256`，更贴合当前已有的手动更新链路，也足以显著降低坏包、残包和篡改包进入替换流程的概率。
- 影响范围：`launcher/services/update_manifest.py`、`launcher/services/local_update.py`、`scripts/generate-update-manifest.py`、`scripts/build-launcher.ps1`、本地更新错误文案，以及后续在线更新/签名能力的包格式基线。
- 后续约束：本地导入更新包默认必须存在合法的 `update-manifest.json`；manifest 中 `packageVersion` 必须与 `version.json.version` 一致；所有实际会被导入的关键分发条目都必须有 manifest 记录且哈希匹配，否则一律在创建备份和替换文件前失败。若后续要提升到发布者身份级别可信度，应在此基础上再叠加数字签名，而不是回退到仅校验版本号。

## 2026-04-11｜在线更新先采用“静态 JSON 检查 + 下载到临时目录 + 复用本地导入链路”的保守方案

- 背景：产品文档已将“检查更新”列为 P1 能力，但如果本轮直接实现“联网下载后自动原地替换”，会同时引入网络、下载、解压、文件占用、替换和回滚的复合风险；而项目已经拥有一套经过测试的本地导入更新安全链路。
- 理由：把在线更新拆成“固定静态 `update.json` 地址检查版本 -> 下载 zip 到 `%TEMP%` -> 解压为临时包目录 -> 交给现有 `LocalUpdateImportService`”，可以最大化复用既有的版本校验、manifest 校验、备份、替换和回滚逻辑，用最小增量补齐用户最需要的联网更新体验。
- 影响范围：`launcher/services/online_update.py`、`LauncherController` 在线更新编排、主界面“检查更新”入口、`OpenClawLauncherApplication` 的交互流程，以及后续真实更新源接入配置。
- 后续约束：在线更新本轮只允许从静态 JSON 地址获取 `version`、`notes` 和 `packageUrl`；下载得到的 zip 必须先解压到 `%TEMP%\OpenClawPortable\updates\`，不得直接绕过本地导入链路原地替换；若后续要做静默更新或后台自动替换，必须单独设计和回归验证。

## 2026-04-11｜在线更新源地址采用“内置默认地址 + 环境变量覆盖”的集中解析策略

- 背景：在线“检查更新”主链路已经落地，但如果更新源地址继续散落在 `OnlineUpdateService` 的默认参数、测试构造器和未来发布脚本里，后续接真实静态地址、做灰度联调或临时切换更新源时就会不断重复改代码，容易出现正式地址和测试地址混用。
- 理由：将更新源解析提炼到独立模块，由 `OnlineUpdateService` 统一复用“显式传入 URL -> 环境变量 `OPENCLAW_PORTABLE_UPDATE_FEED_URL` -> 内置默认地址”的优先级，既能保证正式便携包开箱可用，又能保留本地联调、灰度验证和售后排查时的一次性覆盖能力，且不会把环境变量读取细节扩散到业务流程里。
- 影响范围：`launcher/services/update_feed.py`、`launcher/services/online_update.py`、在线更新测试、后续真实更新源发布脚本与构建配置。
- 后续约束：正式更新地址必须集中维护在 `launcher/services/update_feed.py` 的默认常量中；任何联调、灰度或临时切源都应优先通过 `OPENCLAW_PORTABLE_UPDATE_FEED_URL` 完成，而不是继续在业务代码里散落硬编码；若后续引入 GUI 配置项或远程多渠道策略，也应建立在这一集中解析层之上。

## 2026-04-11｜便携版默认使用当前仓库 GitHub Releases 作为更新包托管源

- 背景：在线检查更新主链路和更新源配置都已就绪，但项目仍缺少一条真正可落地、无需自建服务器的发布路径；与此同时，便携版的更新包并不是 OpenClaw 上游官方 release 结构，而是带有启动器、`version.json`、`update-manifest.json`、内置 Node 和便携目录约束的自有产物。
- 理由：选择当前仓库 `Antonio-bamao/OpenClaw-Portable` 的 GitHub Releases 作为默认托管源，可以用最低运维成本承载 `update.json` 与便携包 zip，同时保持更新链路完全围绕自有包格式展开；相比直接链接 OpenClaw 上游官方 release，这样不会破坏启动器、manifest 校验和本地回滚边界。
- 影响范围：`launcher/services/release_assets.py`、`launcher/services/update_feed.py`、`scripts/build-release-assets.py`、`scripts/build-release-assets.ps1`、发布文档与后续 GitHub Release 维护流程。
- 后续约束：默认更新源固定指向当前仓库 `releases/latest/download/update.json`；每个便携版 Release 至少需要上传 `OpenClaw-Portable-<version>.zip` 与 `update.json` 两个资产；若后续迁移到自有静态站或对象存储，也应保持 `update.json -> packageUrl -> 本地导入链路` 这一主结构不变。

## 2026-04-11｜更新包数字签名采用 Ed25519，签名对象固定为 `update-manifest.json`

- 背景：在补齐 GitHub Releases 托管之后，更新链路已经可以校验版本、哈希清单、备份和回滚，但仍无法证明“这个包确实是发布者签出来的”；如果攻击者能同时替换包内容和 manifest，单靠哈希清单仍缺少发布者身份这一层可信度。
- 理由：用 Ed25519 对 `update-manifest.json` 做 detached signature，可以最小增量地把“发布者身份”叠加到现有 manifest 校验链路上。只要签名可信且 manifest 校验通过，就能同时确认“这份 manifest 是我签的”和“manifest 覆盖的关键文件确实没被改”。相比签整个 zip，这种方式更贴合当前本地导入架构，也更容易测试和维护。
- 影响范围：`launcher/services/update_signature.py`、`launcher/services/local_update.py`、`scripts/generate-update-signing-keypair.py`、`scripts/sign-update-manifest.py`、`scripts/build-release-assets.ps1`、`tests/test_update_signature.py`、`tests/test_local_update.py`、发布侧本地私钥管理。
- 后续约束：发布资产必须包含 `update-signature.json`；本地与在线导入更新时，签名验签发生在 manifest 校验和任何文件替换之前；公钥固定内置到仓库，私钥只允许保存在本地忽略目录或外部安全介质中，绝不能提交进仓库；后续若做轮换，应在 `keyId` 层面显式设计，而不是直接替换旧 key 的语义。
