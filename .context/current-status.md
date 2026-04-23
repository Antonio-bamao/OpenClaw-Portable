# 当前状态

- 当前阶段：Phase 2 真实 OpenClaw Runtime Adapter、在线更新闭环与 launcher-first 渠道接入首轮能力已完成，项目进入“外部验证收口 + 下一版发布准备”阶段。
- 已完成：Phase 1 开发版 MVP、根目录 `.context` 指挥舱、`project-context-os` 独立 Skill 仓库发布、Phase 2 设计计划、`OpenClawRuntimeAdapter` 最小骨架、`mock/openclaw` runtime mode 选择策略、OpenClaw `v2026.4.8` npm runtime 接入、生产依赖安装、真实 gateway adapter 启动/健康检查烟雾验证、`runtime/openclaw/` 构建产物化策略、内置 Node 24 准备脚本、PyInstaller onedir + 真实 runtime dist 烟雾验证、dist 完整时自动选择真实 OpenClaw 的启动策略、缺少运行时/启动超时/提前退出的中文错误提示映射、真实模式下 API Key 缺失的主面板诊断提示、主界面 `status_detail` 渲染与运行时长展示、启动/重启时的等待状态提示、自定义 Provider 缺少接口地址/模型名时的配置诊断提示、dist 构建阶段自动裁剪 `.map/.md/.d.ts` 并验证不破坏真实 runtime、真实 OpenClaw 默认冷启动预算提升到 90 秒、`typescript_sources + test_artifacts` 默认 prune 规则、主界面“导出诊断 / 恢复出厂 / 导入更新包 / 恢复更新备份 / 检查更新”闭环、GitHub Releases 发布资产生成、更新包 Ed25519 数字签名与 keyId 轮换支持、发布维护手册、`v2026.04.5` public latest release、真实 D 盘 U 盘交付 gate 验证通过、飞书 / 微信 / QQ / 企微 launcher-first 渠道接入、飞书 live probe 状态校准与证据采集脚本、飞书 probe 失败态 truthfulness 修正、launcher 中文字体回退 / 标题样式拆分 / 滚动容器修复、微信 / QQ 帮助与状态 UX 加固、QQ 真正 onboarding 流程与微信“确认已扫码”动作、mock runtime 下飞书“连接中”误判修正与状态文案澄清、OpenClaw 简化启动路径、去除启动关键路径飞书 probe 依赖、真实 runtime 自动启动并自动打开 dashboard、HTTP gateway readiness 检查，以及本地源码上的 `210` 项单元测试验证。
- 进行中：真实飞书私聊、微信、QQ、企微的凭证级 E2E 验证，以及多厂商杀软 / SmartScreen 证据收集；本地源码和 `dist/OpenClaw-Portable` 已包含 2026-04-17 至 2026-04-23 的微信 / QQ 加固、真实 onboarding、中文 UI 布局修复、mock 飞书状态修正与启动体验改进，但 GitHub latest 仍停留在 `v2026.04.5`，尚未包含这些后续改动。
- 下一步：优先补齐真实飞书 / 微信 / QQ / 企微凭证联调证据与多厂商杀软 / SmartScreen 证据；如果希望把 2026-04-17 至 2026-04-23 的本地改进对外发布，则基于当前本地源码和 dist 准备下一版 release。
- 阻塞项：外部验证仍依赖真实平台凭证、实际可联通环境以及第三方安全信誉证据，当前本机无法单独清零这些 pending；源码态 `runtime/openclaw` 仍约 0.992GB、93486 文件，其中 `node_modules` 约 0.807GB、`dist` 约 0.17GB，`.ts + .map + .md` 约 295MB。虽然默认 prune 后的 clean dist 已稳定在约 `558.74MB / 25841` 文件、D 盘交付 gate 已验证通过，但多引擎杀软 / SmartScreen 结果仍不能由本机 Defender 基线替代。

## 2026-04-11 Update

- Completed: update package signature verification now supports a trusted public key map keyed by `keyId`; `docs/release-maintenance-playbook.md` documents release maintenance; `v2026.04.2` has been published as a GitHub latest release and its anonymous update feed / zip asset links have been verified.
- Current update chain: online feed -> GitHub Release package download -> local import -> version check -> `update-signature.json` Ed25519 verification -> `update-manifest.json` SHA-256 verification -> backup -> replace -> rollback on failure.
- Current caveat: source now fixes slow launcher button handling by moving long-running actions to background execution, but the already published `v2026.04.2` zip does not include that fix.
- Current audit: `scripts/audit-portable-package.py` reports the current smoke-mutated dist package at about `582.17MB` / `31221` files, with mutable `state/` entries explicitly reported; release zip creation rejects those entries before packaging; runtime prune candidates now show low-risk groups already at `0`, medium-risk TypeScript sources at about `22.49MB`, and test artifacts at about `3.88MB`.
- Next recommended step: run experimental prune + real runtime smoke on TypeScript sources and test artifacts before promoting any new default prune rule.

## 2026-04-12 Runtime Stability Update

- Completed: added `launcher/services/runtime_stability.py`, `scripts/verify-portable-runtime-stability.py`, and `tests/test_runtime_stability.py` to run repeatable real-package stability verification against `dist/OpenClaw-Portable` with isolated `%TEMP%` state roots.
- Root cause fixed: the first real verification attempt failed because the verifier wrote launcher-schema JSON into isolated `state/openclaw.json`; the runner now preserves the package's runtime `state/openclaw.json` / `.env` and prepares the runtime adapter directly without overwriting runtime config.
- Real verification result: `python .\\scripts\\verify-portable-runtime-stability.py --package-root dist\\OpenClaw-Portable --cold-runs 3 --restart-runs 2 --output tmp\\runtime-stability-report.json` passed all 5 runs. Cold starts: `27.61s`, `25.59s`, `28.62s`; restarts: `27.61s`, `25.62s`; max `28.62s`, average `27.01s`.
- Package cleanliness note: verification logs/state were written under `%TEMP%\\OpenClawPortableVerification\\...`; a follow-up `python .\\scripts\\audit-portable-package.py --top 5` confirmed the package still only shows the previously known smoke-mutated state entries and was not additionally polluted by the verifier itself.
- Current recommendation: keep the verifier as the default pre-release stability gate, then rebuild a clean dist only when we are ready to bundle the next release.

## 2026-04-12 Runtime Prune Experiment Update

- Completed: `scripts/prune-portable-runtime.py` now supports experimental `--directory-name` matching so prune dry-runs can align with `portable_audit.py` candidate groups for `test_artifacts`.
- Verified: a rebuilt clean `dist/OpenClaw-Portable` reports `unexpected_state_paths=[]` and `write_risk_directories=[]`; TypeScript dry-run matches `4961` files / `22.49MB`, and test-artifact dry-run matches `740` files / `3.88MB`.
- Verified: the combined experiment package at `tmp/prune-experiments/ts-and-tests` removed `5381` files / `24.26MB`, audits clean with both medium-risk candidate groups reduced to `0`, and passed `python .\\scripts\\verify-portable-runtime-stability.py --package-root tmp\\prune-experiments\\ts-and-tests --cold-runs 3 --restart-runs 2 --output tmp\\prune-experiments\\ts-and-tests-runtime-stability.json` with max `28.62s` and avg `22.50s`.
- Verified: `python -m unittest discover -s tests` now passes `122` tests after the prune tooling extension.
- Next recommended step: either promote these two groups into the default prune path and rerun release-grade verification on a rebuilt clean dist, or keep them experimental while shifting focus to U-disk read/write performance analysis.

## 2026-04-12 Feishu Channel Design Update

- Completed: wrote `docs/superpowers/specs/2026-04-12-feishu-private-chat-channel-design.md` to define the first channel-delivery slice as “Feishu only, launcher-first, private-chat MVP”.
- Scoped: this design intentionally excludes WeChat / QQ / WeCom, group chat, WebUI dual entry, and any Python-side custom message bridge; runtime message flow remains inside OpenClaw runtime/plugin infrastructure.
- Defined: launcher responsibilities, `state/channels/feishu/{config,status}.json` storage model, channel state machine, runtime message path, offline help requirements, Chinese error mapping, diagnosis redaction, and the six MVP acceptance criteria.
- Next recommended step: have the user review the written spec first; if approved, convert it into an implementation plan before touching code.

## 2026-04-12 Feishu Channel Planning Update

- Completed: wrote `docs/superpowers/plans/2026-04-12-feishu-private-chat-channel.md` to turn the approved Feishu private-chat spec into an executable implementation plan.
- Planned: the work is decomposed into launcher pathing/storage, credential validation, runtime projection, runtime config merge, launcher UI, diagnostics/help, and regression coverage.
- Confirmed: the plan assumes reuse of the bundled OpenClaw Feishu extension under `runtime/openclaw/dist/extensions/feishu/` rather than building a separate Python-side bridge.
- Next recommended step: choose execution mode for the plan. Recommended: subagent-driven execution with review between tasks.

## 2026-04-13 Feishu Channel Implementation Update

- Completed: implemented the launcher-first Feishu private-chat MVP slice from the approved plan. The launcher now has Feishu channel storage under `state/channels/feishu/`, credential validation through the Feishu tenant token endpoint, runtime projection into `state/openclaw.json` plus `FEISHU_APP_ID` / `FEISHU_APP_SECRET`, status refresh into `status.json`, a visible Feishu channel card in the main window, controller/app action wiring, diagnostics redaction, and an offline setup guide at `assets/guide/setup-feishu.html`.
- Verified: `python -m unittest discover -s tests` passes `141` tests in the Feishu implementation worktree.
- Scope note: this implementation keeps the agreed MVP boundary: Feishu only, launcher-first, private chat only, no WeChat/QQ/WeCom, no group-chat expansion, and no Python-side message bridge.
- Remaining validation: real end-to-end private chat still requires a real Feishu app credential set and the bundled OpenClaw Feishu runtime extension to be configured in an environment that can reach Feishu.

## 2026-04-13 Local Delivery-Risk Evidence Update

- Completed: pushed local `main` commit `8b1c473` to `origin/main`, so the Feishu private-chat implementation is no longer only local.
- Verified: `python scripts\audit-portable-package.py --package-root dist\OpenClaw-Portable --top 8` reports `558.52MB / 25837` files, required paths present, `unexpected_state_paths=[]`, `write_risk_directories=[]`, and all prune candidate groups at `0`.
- Verified: Windows drive enumeration found no usable removable U-disk target. `F:` is DriveType `2` but has no filesystem/size; `G:` and `H:` are DriveType `3`.
- Verified: Windows Defender is enabled with real-time and IOAV protection enabled; local custom scans of `OpenClawLauncher.exe` and `OpenClaw-Portable-v2026.04.2.zip` completed without command errors, and `Get-MpThreatDetection` returned no detections.
- Next recommended step: attach a real U-disk or provide the target delivery-media path before running read/write and cold-start measurements on removable media; otherwise continue with a documented assessment plan and multi-engine/SmartScreen validation checklist.

## 2026-04-13 Delivery Flow Gate Update

- Completed: added `launcher/services/delivery_gate.py` and `scripts/verify-delivery-flow.py` to provide a single local delivery readiness gate without publishing or mutating product state.
- Covered: the gate checks portable package audit results, release zip/update feed/manifest/signature presence, zip contents, optional runtime stability runs, and explicit pending evidence for Feishu private-chat E2E, removable-media runs, and multi-engine AV/SmartScreen validation.
- Verified: `python -m unittest tests.test_delivery_gate -v` passes `4` delivery-gate tests, including a RED/GREEN regression for release zips missing `update-signature.json`; `python -m unittest discover -s tests` passes `145` tests in the delivery-flow-gate worktree.
- Verified: after regenerating the ignored local `dist/OpenClaw-Portable/update-signature.json` artifact from `.local/update-signing-private-key.txt`, `python scripts\verify-delivery-flow.py --package-root C:\Users\m1591\Desktop\OpenClaw-Portable-1\dist\OpenClaw-Portable --release-dir C:\Users\m1591\Desktop\OpenClaw-Portable-1\dist\release --cold-runs 1 --restart-runs 1 --timeout-seconds 90 --output tmp\delivery-flow-gate-main-dist-rerun.json` returned `status=pending`: audit passed, release assets passed, runtime stability passed, and only external Feishu/U-disk/multi-engine AV evidence remains pending.
- Note: one earlier run hit a transient restart port bind failure; the issue was recorded in `.context/bug-log.md`, and verification should not run real runtime gates in parallel with unit tests.

## 2026-04-14 WeChat / QQ / WeCom Channel Update

- Completed: added a launcher-first social channel slice for WeChat, QQ Bot, and WeCom while keeping the existing Feishu private-chat implementation intact.
- Delivered: `launcher/services/social_channels.py` stores channel config/status under `state/channels/{wechat,qq,wecom}/`, builds runtime config patches for `openclaw-weixin`, bundled `qqbot`, and `wecom`, launches OpenClaw CLI commands for WeChat plugin install / QR login and WeCom plugin install, and exposes redacted channel summaries in diagnostics.
- UI: the main launcher now shows cards for WeChat ClawBot, QQ Bot, and WeCom; the app layer wires install/login/save/test/enable/disable handlers into the controller.
- Verified: `python -m unittest discover -s tests` passes 157 tests after the channel expansion.
- Remaining external validation: real WeChat QR login requires the user's WeChat account to have the ClawBot plugin rollout and network access to install `@tencent-weixin/openclaw-weixin`; QQ requires real QQ Open Platform AppID/AppSecret; WeCom requires real plugin-side credentials and tenant setup.

## 2026-04-16 U-Disk Runtime Cache Update

- Completed: real `D:` removable-media validation is now implemented and verified for the mounted U disk. The U disk package at `D:\OpenClaw-Portable` is synchronized with `dist\OpenClaw-Portable`, audit-clean, and byte/file-count matched at `558.55MB / 25839` files.
- Delivered: removable-drive runtime staging in `OpenClawRuntimeAdapter`. On Windows removable package roots, the launcher stages `runtime/openclaw` into a versioned local temp cache with `robocopy /MT`, then starts the gateway from local cache while preserving U-disk `state/` as the portable data root.
- Delivered: runtime readiness now requires two consecutive successful health checks, fixing a restart false positive seen during delivery-gate verification.
- Verified: `python -m unittest discover -s tests` passes `159` tests. Local dist delivery gate passes package audit, release assets, and runtime stability. D-drive delivery gate with `--cold-runs 1 --restart-runs 1 --removable-media-path D:\OpenClaw-Portable` returns `status=pending` with package audit passed, release assets passed, runtime stability passed (cold `34.72s`, restart `21.72s`), and removable-media evidence passed.
- Remaining external validation: real Feishu private-chat E2E and real WeChat/QQ/WeCom platform credential tests still need user/platform credentials. Multi-engine AV/SmartScreen evidence remains pending; local Defender baseline alone is not a replacement.

### Final 2026-04-16 verification rerun

- `python -m unittest discover -s tests` passes `159` tests. The final real U-disk delivery gate at `D:\OpenClaw-Portable` passes package audit, release assets, runtime stability, and removable-media evidence with cold `31.20s`, restart `21.70s`, max `31.20s`, average `26.45s`. Overall gate status remains `pending` only for external Feishu E2E credentials and multi-engine AV/SmartScreen evidence.

### Final release-asset verification rerun

- After regenerating `dist\release\OpenClaw-Portable-v2026.04.2.zip` and `update.json`, resyncing the rebuilt package to `D:\OpenClaw-Portable`, and rerunning the real D-drive delivery gate, package audit, release assets, runtime stability, and removable-media evidence all pass. Latest final measurements: cold `34.75s`, restart `23.20s`, max `34.75s`, average `28.98s`. Overall status remains `pending` only for external Feishu E2E credentials and multi-engine AV/SmartScreen evidence.

### 2026-04-16 Remote Alignment Update

- Completed: pushed local `main` to `origin/main`, so `ddbb826` (`feat: add wechat qq wecom channels`) and `d1cfb0d` (`fix: cache runtime on removable media`) are now remote-backed.
- Current state: the working tree was clean before the context update; package audit, release assets, runtime stability, and D-drive removable-media evidence are already verified from the final rerun above.
- Remaining external validation: real Feishu private-chat E2E, real WeChat/QQ/WeCom platform credential tests, and multi-engine AV/SmartScreen evidence still require external accounts or third-party validation.
- Next recommended step: collect the remaining external evidence, or start a new release-preparation pass if the remote-backed runtime-cache fix should be included in the next public artifact.

### 2026-04-16 v2026.04.3 Release-Candidate Prep

- Completed: bumped root `version.json` to `v2026.04.3` with build date `2026-04-16`, rebuilt signed release assets, and generated `dist\release\OpenClaw-Portable-v2026.04.3.zip` plus a clean `update.json` pointing at tag `v2026.04.3`.
- Verified: focused update/release suite passed `48` tests; full `python -m unittest discover -s tests` passed `159` tests.
- Verified: local `dist\OpenClaw-Portable` audit passed at `558.55MB / 25839` files, and local delivery gate passed package audit, release assets, and runtime stability with cold `24.14s`, restart `20.59s`, max `24.14s`, avg `22.37s`.
- Verified: `D:\OpenClaw-Portable` was resynced to `v2026.04.3`, audit-clean at `558.55MB / 25839` files, robocopy dry-run showed no remaining differences, and D-drive delivery gate passed package audit, release assets, runtime stability, and removable-media evidence with cold `35.75s`, restart `22.23s`, max `35.75s`, avg `28.99s`.
- Published: Git tag `v2026.04.3` was pushed to origin, GitHub Release `v2026.04.3` was created, and release assets `OpenClaw-Portable-v2026.04.3.zip` plus `update.json` were uploaded.
- Verified public update entry: `https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json` now resolves to `v2026.04.3` and points to the `v2026.04.3` zip; the public zip URL returned HTTP `200`.
- Remaining external validation: real Feishu private-chat E2E, real WeChat/QQ/WeCom platform credential tests, and multi-engine AV/SmartScreen evidence still remain pending.

### 2026-04-17 v2026.04.4 Release And Cleanup Update

- Completed: fixed Windows online-update handling for deep runtime paths. `OnlineUpdateService` now extracts zip entries with Windows long-path handling, local update directory replacement uses `robocopy` on Windows, and update manifest hashing/traversal is long-path safe while preserving existing manifest compatibility.
- Published: source commit `62bd791` is on `main` and `origin/main`, annotated tag `v2026.04.4` exists locally, and GitHub Release `v2026.04.4` was created with public latest-feed verification before cleanup.
- Verified before cleanup: focused update/local-update/manifest/delivery tests passed, full `python -m unittest discover -s tests` passed `162` tests, local delivery gate passed package audit/release-assets/runtime stability, and real online-update smoke upgraded an old package to `v2026.04.4` while preserving state.
- Cleanup: removed temporary validation directories from `D:\ocs-*`, `C:\Users\m1591\ocs-*`, project `tmp`, `build`, `dist\pyinstaller`, `dist\release`, and `OpenClawLauncher.spec`. These were validation/build artifacts, not user runtime files.
- Current local artifact state: `dist\OpenClaw-Portable` remains present and reports `v2026.04.4`; local `dist\release` was intentionally deleted as non-runtime cleanup, while the already-published GitHub Release remains the release source.
- Next recommended step: do not run more U-disk or release rebuild work unless explicitly needed. Remaining product validation is external: real Feishu/WeChat/QQ/WeCom credentials and multi-engine AV/SmartScreen evidence.

### 2026-04-17 Launcher PyInstaller Dependency Fix

- Completed: fixed the packaged launcher crash `No module named '_cffi_backend'` by adding `_cffi_backend` as an explicit PyInstaller hidden import in `scripts/build-launcher.ps1`.
- Guarded: added `tests/test_build_launcher_script.py` so future launcher builds keep the PyNaCl/CFFI runtime dependency included.
- Verified locally: rebuilt `dist\OpenClaw-Portable`, confirmed `_internal\_cffi_backend.cp312-win_amd64.pyd` exists, short-launched `OpenClawLauncher.exe` without the import-time crash, and `python -m unittest discover -s tests` passed `163` tests.
- Current release note: this fix is in local source/build state and still needs a deliberate next release/tag if it should replace the already-published `v2026.04.4` public artifact.

### 2026-04-17 v2026.04.5 Release-Candidate Prep

- Completed: bumped root `version.json` to `v2026.04.5` with build date `2026-04-17`, rebuilt signed release assets, and generated `dist\release\OpenClaw-Portable-v2026.04.5.zip` plus `dist\release\update.json`.
- Included fix: this hotfix release candidate includes commit `6710fd3` (`fix: include cffi backend in launcher build`) so packaged launcher builds bundle `_cffi_backend` and avoid the previous import-time crash.
- Verified: `python -m unittest discover -s tests` passed `163` tests; `python scripts\audit-portable-package.py --package-root dist\OpenClaw-Portable --top 8` passed with `558.73MB / 25840` files and no warnings; `dist\OpenClaw-Portable\_internal\_cffi_backend.cp312-win_amd64.pyd` exists; short-launching `OpenClawLauncher.exe` returned `started_without_import_crash`.
- Verified delivery gate: `python scripts\verify-delivery-flow.py --package-root dist\OpenClaw-Portable --release-dir dist\release --cold-runs 1 --restart-runs 1 --timeout-seconds 90 --output tmp\delivery-flow-gate-v2026.04.5.json` returned `status=pending` with package audit, release assets, and runtime stability passed. Runtime cold start was `25.12s`, restart was `23.11s`, max was `25.12s`, average was `24.12s`.
- Current release note: assets are locally ready for publication, but Git tag and GitHub Release still need to be created and verified.
- Remaining external validation: real Feishu/WeChat/QQ/WeCom credential E2E and multi-engine AV/SmartScreen evidence remain pending.

### 2026-04-17 v2026.04.5 Published

- Completed: committed release preparation as `c30e440` (`chore: prepare v2026.04.5 release`), pushed `main`, created and pushed annotated tag `v2026.04.5`, and published GitHub Release `v2026.04.5`.
- Uploaded assets: `OpenClaw-Portable-v2026.04.5.zip` (`205700820` bytes) and `update.json` (`251` bytes).
- Verified public update entry: `https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json` resolves to version `v2026.04.5` and points to the `v2026.04.5` zip asset.
- Verified public zip access: `curl.exe -L -I` against the `v2026.04.5` zip URL returned HTTP `200`.
- Current local artifact state: `dist\OpenClaw-Portable` and `dist\release` are present for `v2026.04.5`; `dist\release` now mirrors the public release assets.
- Remaining external validation: real Feishu/WeChat/QQ/WeCom credential E2E and multi-engine AV/SmartScreen evidence remain pending.

### 2026-04-17 WeChat / QQ Integration Hardening

- Completed: tightened the launcher-first WeChat / QQ channel slice without requiring real platform credentials. WeChat now refreshes launcher state from likely OpenClaw Weixin runtime status files, so a successful QR/login status can move the launcher from `待扫码` to `待启用` or `已启用`. QQ now refuses enable/test when a real packaged OpenClaw runtime is present but the bundled `qqbot` extension is missing.
- Delivered: QQ runtime projection now also exports `QQBOT_APP_ID` and `QQBOT_CLIENT_SECRET`, matching the OpenClaw QQ Bot docs' env fallback while preserving the existing config patch.
- Verified: `python -m unittest tests.test_social_channel_service -v` passed `7` tests; `python -m unittest tests.test_launcher_controller tests.test_launcher_app tests.test_launcher_bootstrap -v` passed `47` tests; `python -m unittest discover -s tests` passed `165` tests.
- Verified package/runtime evidence: both source runtime and current dist contain `runtime\openclaw\dist\extensions\qqbot\openclaw.plugin.json`.
- Packaged smoke: rebuilt local `dist\OpenClaw-Portable` with `scripts\build-launcher.ps1`; `python scripts\audit-portable-package.py --package-root dist\OpenClaw-Portable --top 5` passed at `558.73MB / 25839` files with no warnings; short-launching `OpenClawLauncher.exe` returned `started_without_import_crash`.
- Current release note: this hardening is committed and present in the local rebuilt dist, but a new public package/release is still needed if it should ship beyond this machine.

### 2026-04-17 WeChat / QQ Help And Status UX Hardening

- Completed: added packaged local help pages for WeChat and QQ under `assets/guide/`, plus launcher help buttons for both cards.
- Delivered: the launcher now exposes `接入帮助` on the WeChat and QQ cards, opens packaged HTML help pages through the existing browser path, refreshes the main view after the WeChat login command starts, and makes the WeChat `pending_enable` / QQ `missing_runtime_plugin` messages more action-oriented.
- Verified: `python -m unittest tests.test_social_channel_service tests.test_launcher_bootstrap tests.test_launcher_app tests.test_launcher_controller -v` passed `58` tests; `python -m unittest discover -s tests` passed `169` tests.
- Packaged smoke: rebuilt local `dist\OpenClaw-Portable`; `dist\OpenClaw-Portable\assets\guide\setup-wechat.html` and `dist\OpenClaw-Portable\assets\guide\setup-qq.html` both exist; `python scripts\audit-portable-package.py --package-root dist\OpenClaw-Portable --top 5` passed at `558.74MB / 25841` files with no warnings; short-launching `OpenClawLauncher.exe` returned `started_without_import_crash`.
- Current release note: this UX hardening is in local source and rebuilt dist, but still needs a deliberate next release if it should become the public downloadable artifact after `v2026.04.5`.

### 2026-04-18 WeChat / QQ Real Onboarding Hardening

- Completed: moved the launcher-owned QQ flow one step closer to real runtime onboarding and added an explicit WeChat login confirmation action.
- Delivered: QQ enable now runs the documented `openclaw channels add --channel qqbot --token "AppID:AppSecret"` flow through the existing command runner before the launcher marks the channel enabled; QQ stores a credential fingerprint so unchanged credentials do not rerun onboarding, while changed credentials clear the prior onboarding marker. WeChat now exposes `确认已扫码`, which immediately refreshes runtime login state instead of relying only on passive refresh.
- Delivered: QQ onboarding failures now surface as `enable_failed` launcher state and keep the channel disabled; the WeChat confirm action is wired through the existing background-action path and included in the rebuilt packaged launcher UI.
- Verified: `python -m unittest tests.test_social_channel_service tests.test_launcher_controller tests.test_launcher_app tests.test_launcher_bootstrap -v` passed `63` tests; `python -m unittest discover -s tests` passed `174` tests.
- Packaged smoke: `scripts\build-launcher.ps1` rebuilt local `dist\OpenClaw-Portable`; `python scripts\audit-portable-package.py --package-root dist\OpenClaw-Portable --top 5` passed at `558.74MB / 25841` files with no warnings; short-launching `dist\OpenClaw-Portable\OpenClawLauncher.exe` returned `started_without_import_crash`.
- Current release note: this real-onboarding hardening is present in local source and rebuilt dist only; GitHub latest remains `v2026.04.5` until a new release is prepared and published.

### 2026-04-18 Feishu Probe-Based Status Hardening

- Completed: tightened the launcher-owned Feishu status model so `已连接` is no longer inferred only from the overall runtime process being `running`.
- Delivered: `LauncherController` now attempts `openclaw channels status --probe --json` while the real OpenClaw runtime is running and the Feishu channel is enabled/configured, and `FeishuChannelService` maps `channelAccounts.feishu[].probe` / `lastError` / `configured` into launcher states. Probe success keeps `connected`; probe failure now surfaces `connection_failed`; `configured=false` is treated as `needs_reconfigure`.
- Verified: `python -m unittest tests.test_feishu_channel_service` passed `8` tests; `python -m unittest tests.test_launcher_controller` passed `24` tests; `python -m unittest discover -s tests` passed `178` tests.
- Remaining external validation: real Feishu private-chat E2E still requires a real local credential set plus a reachable Feishu environment; this round improves truthfulness of launcher status once those credentials are exercised, but does not by itself produce external E2E evidence.

### 2026-04-18 Feishu Probe Evidence Script

- Completed: added a dedicated local verifier for Feishu live-probe evidence so the remaining real E2E gap is easier to close once credentials are present.
- Delivered: `launcher/services/feishu_probe.py` now builds a redacted Feishu probe evidence summary from `openclaw channels status --probe --json`, and `scripts/verify-feishu-channel.py` emits JSON evidence plus a non-zero exit code on failure.
- Verified: `python -m unittest tests.test_feishu_probe` passed `4` tests; `python -m unittest discover -s tests` passed `182` tests; running `python scripts\verify-feishu-channel.py` in the current repo correctly failed with `Feishu channel is not enabled in local launcher state.` because there is still no local saved Feishu config.
- Remaining external validation: this script does not remove the need for real credentials or a reachable Feishu environment; it reduces the remaining work to “save/enable/start runtime, then capture evidence” instead of manual CLI spelunking.

### 2026-04-18 Feishu Probe Failure Truthfulness Follow-up

- Completed: closed the remaining fallback where a running OpenClaw process could still leave Feishu shown as `connected` if `channels status --probe --json` failed, returned empty output, or produced non-JSON text.
- Delivered: `LauncherController` now carries probe-attempt failure details into `FeishuChannelService`, and the service treats “probe attempted but no valid Feishu payload” as `connection_failed` instead of silently falling back to the optimistic runtime-running branch.
- Verified: `python -m unittest tests.test_feishu_channel_service tests.test_launcher_controller -v` passed `35` tests; `python -m unittest discover -s tests` passed `185` tests; `python scripts\verify-feishu-channel.py --output tmp\feishu-e2e-evidence.json` still correctly failed with `Feishu channel is not enabled in local launcher state.` because no local Feishu credentials are saved/enabled yet.
- Remaining external validation: the code path is now stricter and more truthful, but producing a passing Feishu E2E artifact still requires real credentials plus a reachable Feishu environment.
