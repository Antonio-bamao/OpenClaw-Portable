# OpenClaw Portable `.context` 使用说明

`.context/` 是 OpenClaw Portable 的项目指挥舱，不是附属文档。只要开始真实实施、补功能、修 Bug、调整架构、打包发布或做售后能力，就必须先读并更新这里。

## 读取顺序

1. 先读 `current-status.md`，确认当前阶段、正在做什么、下一步和阻塞项。
2. 再读 `master-plan.md`，确认全局阶段、里程碑、验收标准和依赖关系。
3. 再读 `task-breakdown.md`，确认当前优先级与边界。
4. 涉及历史判断时读 `decisions.md`、`bug-log.md`、`risk-register.md`。

## 维护规则

1. 每完成一个明确步骤，必须追加 `work-log.md`。
2. 每遇到会影响质量、判断、节奏或打包交付的异常，必须追加 `bug-log.md`，并写清根因与预防。
3. 每做出高影响决策，必须更新 `decisions.md`，避免后续重复讨论。
4. 每次会话结束前，必须刷新 `current-status.md`，保证下次开工可以无缝接续。
5. 阶段变更、范围变更、验收标准变更时，必须同步更新 `master-plan.md` 与 `task-breakdown.md`。

## 本项目特别约束

- 用户画像优先面向中文非技术用户，任何实现都优先考虑“插上即用、双击启动、零命令行”。
- 桌面端采用 `PySide6 + 自定义主题`，避免商业授权风险。
- 运行时路径、配置路径、缓存路径必须遵守便携版约束：
  - `runtime/` 承载运行时与插件
  - `state/` 承载配置、会话、渠道状态
  - `%TEMP%\\OpenClawPortable\\` 承载日志与缓存
- 在真实 OpenClaw runtime 接入前，`MockRuntimeAdapter` 仍是开发占位方案，但所有接口设计都要以未来平滑替换为前提。

## 结束会话前检查

在声明“本轮完成”前，至少完成以下动作：

1. 更新 `work-log.md`
2. 如有异常，更新 `bug-log.md`
3. 如有关键判断，更新 `decisions.md`
4. 更新 `current-status.md`
5. 运行 `project-context-os` 的 `validate_context.py`
