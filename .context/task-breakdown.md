# 任务拆解

## 当前优先级

1. 维护项目上下文系统与摘要一致性
   - 保持 `.context/current-status.md`、`.context/task-breakdown.md`、`.context/work-log.md` 与实际交付状态同步
   - 明确区分“已公开发布的 `v2026.04.5`”与“仅在本地源码 / dist 中存在、尚未公开发布的 2026-04-17/18 微信 / QQ 改进”
   - 当外部 E2E 证据补齐或下一版 release 发出时，及时更新摘要，避免旧阶段表述误导后续工作
2. 补齐外部验证证据
   - 用真实飞书应用凭证完成私聊 E2E
   - 用真实微信账号完成二维码登录联调，用真实 QQ Open Platform 凭证完成 QQ Bot 联调，并在可用时补企业微信凭证验证
   - 收集多厂商杀软 / SmartScreen 信誉证据，补齐当前 delivery gate 中仍为 `pending` 的外部检查项
3. 决定并准备下一版公开发布
   - 若要让用户拿到 2026-04-17/18 的微信 / QQ 帮助、状态 UX 与真实 onboarding 改进，则基于当前源码和 `dist/OpenClaw-Portable` 准备 post-`v2026.04.5` release
   - 发版前复用现有 `scripts/verify-delivery-flow.py`、包审计、签名、release 资产与公开下载入口验证流程
   - 若暂不发版，则把当前重点留在外部凭证联调和安全信誉证据收集，不重复做无收益的重建或 U 盘验证
4. 持续关注交付风险与体积纪律
   - 保持 `runtime/openclaw` 大体积风险可见：源码态仍约 `0.992GB / 93486` 文件，clean dist 当前约 `558.74MB / 25841` 文件
   - 延续默认 prune、release state 清洁检查、U 盘本地缓存启动和在线更新长路径兼容等既有交付纪律
   - 在没有新目标时不额外扩大本地验证残留，避免再次把临时验证目录误当成交付产物

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

## 2026-04-17 WeChat / QQ Integration Hardening Update

- Completed: strengthened the existing launcher-first WeChat and QQ channel implementation.
- Delivered: WeChat launcher state can now refresh from likely OpenClaw Weixin runtime status files and recognize logged-in QR state; QQ validation now checks for the bundled `qqbot` runtime extension when a real runtime tree is present; QQ projection now passes `QQBOT_APP_ID` and `QQBOT_CLIENT_SECRET` runtime env vars in addition to the existing config patch.
- Verified: targeted social/controller/app/UI tests passed, full `python -m unittest discover -s tests` passed `165` tests, local `dist\OpenClaw-Portable` was rebuilt, package audit passed, and EXE short-launch smoke passed.
- Next: cut a new release only if the public artifact must include this WeChat / QQ hardening; otherwise continue with real WeChat QR and QQ Open Platform credential E2E when those accounts are available.

## 2026-04-17 WeChat / QQ Help And Status UX Update

- Completed: added launcher-visible `接入帮助` entrypoints and packaged WeChat / QQ setup HTML pages.
- Delivered: WeChat help button opens packaged `setup-wechat.html`; QQ help button opens packaged `setup-qq.html`; WeChat login completion messaging now explicitly tells the user to click `启用微信`; QQ packaged-runtime failure now renders as `缺少扩展` instead of a generic unknown state.
- Verified: focused launcher/service/controller verification passed `58` tests; full `python -m unittest discover -s tests` passed `169` tests; rebuilt local `dist\OpenClaw-Portable` includes both help pages and still passes package audit plus EXE short-launch smoke.
- Next: if this UX pass should ship publicly, prepare the next release/tag; otherwise keep moving on real WeChat QR and QQ credential E2E when account inputs are available.

## 2026-04-18 WeChat / QQ Real Onboarding Update

- Completed: extended the launcher-owned channel flow so QQ enable performs real onboarding and WeChat has an explicit post-QR confirmation step.
- Delivered: `SocialChannelService` now exposes QQ onboarding commands plus credential fingerprint tracking; `LauncherController.enable_qq_channel()` validates, runs onboarding on first enable for a credential set, keeps QQ disabled on command failure, and only skips onboarding when the saved credential fingerprint matches. The launcher UI/app now exposes `确认已扫码` and routes it through `confirm_wechat_channel_login()`.
- Verified: focused social/controller/app/UI verification passed `63` tests; full `python -m unittest discover -s tests` passed `174` tests; rebuilt local `dist\OpenClaw-Portable` passed package audit at `558.74MB / 25841` files; packaged EXE short-launch smoke still returned `started_without_import_crash`.
- Next: use real QQ Open Platform credentials and a real WeChat QR login to collect E2E evidence, or cut the next public release if this launcher-owned onboarding behavior should ship broadly.
