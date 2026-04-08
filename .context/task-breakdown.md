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
   - 下一步补充真实 runtime 首启等待状态、进一步的 Provider 配置诊断和运行时瘦身评估
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
