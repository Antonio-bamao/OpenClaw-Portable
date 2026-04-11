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

- Completed: update package signing now supports key rotation through a trusted `keyId -> public key` map, the release maintenance playbook documents release operations, `v2026.04.2` has been published/verified through GitHub latest release assets, and the launcher now protects long-running buttons with background execution plus busy states.
- Next: publish a `v2026.04.3` hotfix if the release package needs the UI responsiveness fix, or return to runtime slimming / U disk performance work.
