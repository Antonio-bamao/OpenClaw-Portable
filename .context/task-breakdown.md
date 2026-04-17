# 任务拆解

## 当前优先级

1. 稳定项目上下文系统
   - 补齐 `.context` 的计划、状态、日志、Bug、决策和风险文件
   - 让后续所有实现都能基于上下文接续，而不是重新理解项目
2. 启动 Phase 2 真实 runtime 适配
   - 固化原生 Windows + Node 24 优先路线
   - 新增真实 runtime adapter 设计与实施计划
   - 先写 adapter 契约测试，再实现最小骨架
   - 已使用 npm 构建包准备 OpenClaw `v2026.4.8` 到本地 `runtime/openclaw/`
   - 已明确真实启动命令、健康检查入口与环境变量映射
   - 将 `runtime/openclaw/` 作为构建产物，通过 `scripts/prepare-openclaw-runtime.ps1` 重建
   - 已准备内置 Node 24，并验证 onedir 便携包可携带真实 runtime 启动 gateway
   - 已补充自动 `runtime_mode` 选择入口，完整 dist 默认进入真实 OpenClaw，开发态缺失 runtime 时回退 mock
   - 已补充缺少运行时、启动超时、提前退出的中文错误提示映射
   - 已补充真实模式下 API Key 缺失的主面板诊断提示
   - 已补充主面板 `status_detail` 渲染与运行时长展示
   - 已补充真实 runtime 首启/重启时的等待状态提示
   - 已补充自定义 Provider 缺少接口地址/模型名时的配置诊断
   - 已重新完成源码态真实 adapter smoke、PyInstaller onedir 构建与 dist 侧真实 adapter smoke
   - 已量化 runtime/openclaw 体积分布：node_modules 约 0.807GB、dist 约 0.17GB、.ts + .map + .md 约 295MB
   - 已在 dist 构建阶段安全裁剪 `.map/.md/.d.ts`，累计释放约 243.21MB，裁剪后 dist/runtime/openclaw 约 0.754GB / 52875 文件
   - 已先将真实 OpenClaw 默认冷启动预算放宽到 90 秒并同步等待态提示
   - 已补充 pruning CLI 的实验性 `--pattern` 入口，并完成 `plain .ts / .mts / .cts` 的首轮 dry-run 与单次 dist smoke
   - 已补充主界面“导出诊断”入口与脱敏诊断包导出
   - 已补充主界面“恢复出厂”入口，安全重置启动器配置和本地临时状态
  - 已补充主界面“导入更新包”入口与本地更新包导入 / 自动备份 / 失败回滚闭环，默认不覆盖 `state/`
  - 已补充主界面“恢复更新备份”入口与从 `state/backups/updates/` 恢复旧版本 / 恢复前再次备份当前版本 / 失败自动回滚闭环，默认仍不覆盖 `state/`
  - 已补充“导入更新包”前的严格合法性校验：要求 `version.json` 合法、至少包含一项真实分发内容，且更新包版本必须严格高于当前版本；同版本与旧版本会在替换前被拦住，旧版本统一引导走“恢复更新备份”
  - 已补充 `update-manifest.json` 离线完整性清单：构建产物自动生成关键分发内容的 `SHA-256` manifest，本地导入更新包时会在替换前强制校验 manifest 版本、一致性和关键条目哈希
  - 已补充“检查更新”主链路：从固定静态 `update.json` 地址检查新版本、下载 zip 到 `%TEMP%\OpenClawPortable\updates\`、解压为临时包目录，并交给现有本地导入链路完成版本校验、manifest 校验、备份、替换和回滚
  - 已补充真实更新源接入配置：在线更新源地址已集中到 `launcher/services/update_feed.py`，按“显式传入 URL -> `OPENCLAW_PORTABLE_UPDATE_FEED_URL` -> 内置默认地址”解析，默认正式地址与联调覆盖不再散落在业务代码里
  - 已补充 GitHub Releases 发布资产生成：新增发布侧脚本与共享元数据模块，当前可以为仓库 `Antonio-bamao/OpenClaw-Portable` 自动生成 `OpenClaw-Portable-<version>.zip` 和 `update.json`，并把默认更新源指向当前仓库 `releases/latest/download/update.json`
  - 已补充更新包数字签名：新增 `update-signature.json`、Ed25519 验签模块、本地忽略的私钥文件路径 `.local/update-signing-private-key.txt`、以及发布脚本里的签名步骤；更新导入现在会先验签再验 manifest
  - 已补发布维护手册 `docs/release-maintenance-playbook.md`：覆盖 GitHub Release 资产上传、发布说明维护、签名私钥备份/恢复与 keyId 轮换；已完成 `v2026.04.2` GitHub latest release 演练并验证匿名 `update.json` 与 zip 资产可访问
  - 已补启动器长耗时按钮的后台执行与重复点击保护：真实 runtime 启停、在线检查更新、下载导入、导入更新包和恢复更新备份不再直接阻塞 UI 主线程
  - 已补便携交付包只读审计工具：`scripts/audit-portable-package.py` 可输出总大小、文件数、最大目录、必需路径缺失和写入风险目录；当前 dist 约 `582.17MB` / `31221` 文件，必需路径齐全，剩余写入风险为 `state/logs`
  - 已补 release zip 前运行态 state 清洁检查：审计报告会列出 smoke 后 dist 中的可变 `state/` 条目，发布 zip 生成会拒绝 `state/provider-templates` 之外的 state 内容
  - 已补 runtime 裁剪候选报告：审计 JSON 现在按风险分组输出 `source_maps`、`markdown_docs`、`type_declarations`、`typescript_sources`、`test_artifacts`；当前中风险候选约为 TypeScript sources `22.49MB`、test artifacts `3.88MB`
3. 推进 Phase 1 收尾项
   - 诊断导出脚本
   - 重置配置脚本
   - 帮助页与 README/免责声明的一致性整理
   - 打包产物目录完整性核对
4. 预研 Phase 3 渠道能力
   - 梳理微信、飞书、QQ、企微的接入前置条件
   - 设计状态存储与风险提示

## 责任边界

- UI 层：负责展示状态、引导配置、触发动作，不直接持有进程控制与配置逻辑。
- 服务层：负责编排配置、引导、状态加载与视图模型。
- 运行时适配层：负责 mock / real runtime 的准备、启停、健康检查、URL 解析与异常退出检测。
- 便携路径层：负责项目根目录、临时目录、日志目录、配置目录的一致性。
- `.context` 系统：负责项目记忆、节奏控制、Bug 复盘与后续接续。

## 依赖关系

- 真实 runtime 接入依赖于上游版本锁定与本地打包策略明确。
- 渠道管理依赖于 Phase 2 的真实 runtime 能承载插件与状态同步。
- 售后与更新能力依赖于 Phase 2/3 稳定后再补统一诊断模型与回滚机制。
- 任何新的功能实施前，都依赖 `.context/current-status.md` 与 `.context/master-plan.md` 保持同步。

## 2026-04-11 Update

- Completed: update package signing now supports key rotation through a trusted `keyId -> public key` map, the release maintenance playbook documents release operations, `v2026.04.2` has been published/verified through GitHub latest release assets, the launcher now protects long-running buttons with background execution plus busy states, package auditing is available through `scripts/audit-portable-package.py`, release zip generation rejects mutable state entries, and runtime prune candidates are quantified in audit output.
- Next: experimentally prune TypeScript sources and test artifacts on a clean dist, then run real runtime smoke before promoting any new default prune rule.

## 2026-04-12 Update

- Completed: runtime stability verification is now an explicit task outcome, with `scripts/verify-portable-runtime-stability.py` exercising repeated cold starts and restarts against a real portable package while isolating state/logs under `%TEMP%`.
- Verified: the verifier now preserves runtime-native `state/openclaw.json` and optional `.env` instead of writing launcher-schema config into the isolated state root.
- Verified: `python -m unittest discover -s tests` now passes `120` tests, and the real `dist/OpenClaw-Portable` verification run passed `3` cold starts plus `2` restarts with a max startup time of `28.62s`.
- Next: keep runtime stability verification in the delivery checklist, continue with stability-first hardening and packaging discipline, and defer any new release rebuild until the remaining delivery work is complete.

## 2026-04-12 Runtime Prune Experiment Update

- Completed: runtime prune experiments now support both filename patterns and explicit directory-name matching through `scripts/prune-portable-runtime.py --directory-name ...`, so the experiment tool can match `portable_audit.py`'s `test_artifacts` semantics instead of under-counting directory-based test files.
- Verified: on a rebuilt clean `dist/OpenClaw-Portable`, TypeScript dry-run matches `4961` files / `22.49MB`, and test-artifact dry-run matches `740` files / `3.88MB`.
- Verified: the combined experiment package `tmp/prune-experiments/ts-and-tests` removed `5381` files / `24.26MB`, stayed audit-clean, and passed `3` cold starts plus `2` restarts with max startup time `28.62s` and average `22.50s`.
- Verified: `python -m unittest discover -s tests` now passes `122` tests after the prune tooling extension.
- Next: if we want to convert this evidence into a shipping improvement, promote `typescript_sources` + `test_artifacts` into the default prune path, rebuild a clean dist, and rerun the release-grade stability gate before touching the next release.

## 2026-04-13 Feishu Channel Update

- Completed: Feishu private-chat channel MVP implementation is now the active Phase 3 delivery result.
- Delivered: canonical Feishu channel state paths, channel config/status JSON service, tenant-token credential test, runtime config/env projection, runtime config merge into `state/openclaw.json`, Feishu status refresh, launcher view model, controller save/test/enable/disable APIs, main-window Feishu card, app action bindings, diagnostics redaction, and offline setup help.
- Verified: full test suite passes with `python -m unittest discover -s tests` at `141` tests.
- Next: perform real Feishu private-chat E2E validation with actual app credentials, then decide whether to prepare a new release build or continue with U-disk and anti-virus delivery risk work.

## 2026-04-13 Local Delivery-Risk Evidence Update

- Completed: pushed the Feishu implementation commit to `origin/main`, reran the portable package audit on the current clean dist, enumerated local drive types, and ran local Windows Defender custom scans on the launcher EXE plus the existing release zip.
- Verified: clean dist remains at about `558.52MB / 25837` files with no required-path gaps, no mutable release state, no write-risk directories, and no remaining prune-candidate groups.
- Verified: no usable removable U-disk target is currently mounted; `F:` is removable but has no filesystem/size, while `G:` and `H:` are fixed disks.
- Verified: Windows Defender is enabled and local custom scan did not produce threat detections for `dist/OpenClaw-Portable/OpenClawLauncher.exe` or `dist/release/OpenClaw-Portable-v2026.04.2.zip`.
- Next: run real removable-media read/write and cold-start measurements once a usable U-disk is available; keep Defender results as a local baseline only, not a replacement for SmartScreen reputation or multi-engine AV validation.

## 2026-04-13 Delivery Flow Gate Update

- Completed: added `scripts/verify-delivery-flow.py` as the release-readiness command that ties together package audit, release asset checks, optional runtime stability, and external evidence tracking.
- Verified: local package/release/runtime checks can now be run as one JSON-producing gate. On the current main-worktree dist, the gate reaches `status=pending` rather than `failed` once the ignored local signature artifact is regenerated.
- Pending by design: real Feishu private-chat E2E, removable-media performance/cold-start evidence, and multi-engine AV/SmartScreen validation still need outside inputs.
- Next: merge the gate to `main`; then run it before any next release build, using higher runtime run counts for release-grade verification and passing evidence paths when real external validation artifacts exist.

## 2026-04-14 WeChat / QQ / WeCom Channel Update

- Completed: expanded Phase 3 channel support beyond Feishu with a launcher-first social channel service for WeChat ClawBot, QQ Bot, and WeCom.
- Delivered: WeChat plugin install command (`@tencent-weixin/openclaw-weixin@latest`), WeChat QR login command (`openclaw-weixin`), QQ Bot AppID/AppSecret config projection, WeCom plugin install command (`@wecom/wecom-openclaw-plugin@latest`), WeCom credential projection, channel status/config persistence, UI cards, controller/app handlers, and diagnostics redaction.
- Verified: targeted channel/controller/UI/diagnostics tests pass, and full `python -m unittest discover -s tests` passes 157 tests.
- Next: run a real WeChat QR login on the user's machine with the already-installed WeChat ClawBot plugin, then test QQ and WeCom with real platform credentials.

## 2026-04-12 Default Runtime Prune Update

- Completed: default runtime pruning now includes `typescript_sources` and `test_artifacts`, with CLI semantics kept safe as “no args => default prune, explicit args => experiment-only overrides”.
- Verified: `powershell -ExecutionPolicy Bypass -File .\\scripts\\build-launcher.ps1` now reports default prune removal of `30904` files / `165.19MB`, and the rebuilt clean `dist/OpenClaw-Portable` audits at about `558.52MB / 25837` files with no mutable state or write-risk warnings.
- Verified: `python .\\scripts\\verify-portable-runtime-stability.py --package-root dist\\OpenClaw-Portable --cold-runs 3 --restart-runs 2 --output tmp\\runtime-stability-report-default-prune.json` passed `3` cold starts plus `2` restarts with max `26.64s` and average `24.77s`.
- Verified: `python -m unittest discover -s tests` remains green at `122` tests.
- Next: shift the active delivery focus to U-disk read/write performance and anti-virus false-positive risk assessment; when ready to cut the next release, reuse this default-pruned clean dist as the new build baseline.

## 2026-04-16 U-Disk Delivery Update

- Completed: copied the rebuilt portable package to the mounted `D:` U disk and verified that source and U-disk package match exactly (`25839` files, `558.55MB`).
- Completed: fixed D-drive runtime startup by staging OpenClaw runtime files to a local temp cache when the package root is removable.
- Completed: fixed restart readiness by requiring two consecutive gateway health checks.
- Verified: D-drive delivery gate now passes package audit, release assets, runtime stability, and removable-media evidence. Latest D-drive runtime measurements: cold `34.72s`, restart `21.72s`.
- Next: use real Feishu/WeChat/QQ/WeCom credentials to clear channel E2E; collect multi-engine AV/SmartScreen evidence if the product needs stronger public-delivery confidence. Consider runtime archive packaging later to reduce first-cache preparation cost on very slow U disks.

## 2026-04-16 Remote Alignment Update

- Completed: pushed the local `main` implementation commits for WeChat/QQ/WeCom channels and removable-media runtime caching to `origin/main`.
- Verified: push advanced the remote from `f499fa8` to `d1cfb0d`; the final local verification set remains valid and documented in `.context/current-status.md`.
- Next: no local-only implementation commits remain for this slice once this context update is committed and pushed. Remaining tasks require external credentials/evidence or a deliberate next release-preparation pass.

## 2026-04-16 v2026.04.3 Release-Candidate Update

- Completed: prepared a local `v2026.04.3` release candidate containing the social-channel expansion and removable-media runtime-cache fix.
- Verified: `dist\release\OpenClaw-Portable-v2026.04.3.zip` and `dist\release\update.json` exist locally; local and D-drive delivery gates pass all non-external checks, with D-drive runtime cold `35.75s` and restart `22.23s`.
- Completed: published `v2026.04.3` as a GitHub Release with `OpenClaw-Portable-v2026.04.3.zip` and `update.json`; the public latest feed now resolves to `v2026.04.3`.
- Next: collect external platform and AV/SmartScreen evidence. No local release-packaging action is pending for `v2026.04.3`.

## 2026-04-17 v2026.04.5 Hotfix Release-Candidate Update

- Completed: prepared a local `v2026.04.5` hotfix release candidate so the public artifact can include the packaged-launcher `_cffi_backend` fix from commit `6710fd3`.
- Verified: `dist\release\OpenClaw-Portable-v2026.04.5.zip` and `dist\release\update.json` exist locally; `update.json` points to the `v2026.04.5` GitHub Release asset URL.
- Verified: full tests passed at `163` tests, portable package audit passed at `558.73MB / 25840` files, the packaged `_cffi_backend.cp312-win_amd64.pyd` exists, short-launching the EXE did not reproduce the import crash, and the local delivery gate passed package audit, release assets, and runtime stability.
- Completed: committed and pushed the `v2026.04.5` version/context update, created and pushed the annotated `v2026.04.5` tag, published the GitHub Release assets, verified the public latest feed resolves to `v2026.04.5`, and verified the public zip URL returns HTTP `200`.
- Next: collect external platform credential E2E evidence and multi-engine AV/SmartScreen evidence when available. No local release-packaging action is pending for `v2026.04.5`.
