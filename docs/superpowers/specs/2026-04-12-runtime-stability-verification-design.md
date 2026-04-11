# 真实运行稳定性验证设计

## 背景

当前项目已经具备：

- 真实 OpenClaw runtime 接入
- onedir 便携包构建
- 冷启动预算放宽到 90 秒
- 主界面长耗时按钮后台执行
- 发布资产生成、签名、在线更新和回滚链路

但在“可以交付给用户长期使用”这个目标上，还缺少一套可重复执行的稳定性验证。现在我们知道单次 smoke 可以成功，也知道冷启动曾逼近 60 秒边界，但还没有一份结构化工具来回答下面这些问题：

- 冷启动是否稳定
- 重启是否稳定
- 多轮运行后端口、健康检查和退出是否稳定
- 一旦失败，日志和错误提示是否足够定位

## 目标

本轮补一个只读验证工具，用结构化 JSON 报告记录真实 runtime 的稳定性表现：

- 支持多轮冷启动验证
- 支持多轮重启验证
- 记录每轮耗时、端口、健康状态、失败信息
- 汇总成功率、最长耗时、平均耗时
- 在失败时给出日志路径提示，便于售后和继续排查

## 非目标

- 本轮不修改产品默认行为
- 本轮不变更 runtime timeout 策略
- 本轮不裁剪 runtime
- 本轮不更新 release
- 本轮不实现 GUI 里的“稳定性验证”按钮
- 本轮不做 U 盘真实设备 I/O 基准压测

## 用户场景

维护者在仓库根目录运行一个验证脚本，例如：

```powershell
python .\scripts\verify-portable-runtime-stability.py --package-root dist\OpenClaw-Portable --cold-runs 3 --restart-runs 2
```

脚本会：

1. 基于指定便携包目录构造 `PortablePaths`
2. 使用独立的临时 state / temp 根目录，避免污染包内 `state/`
3. 连续执行多轮冷启动和重启
4. 对每轮记录：
   - 轮次
   - 动作类型（cold_start / restart）
   - 是否成功
   - 启动或重启耗时
   - 最终监听端口
   - 健康检查结果
   - 失败错误信息
   - 相关日志路径
5. 最后输出一份 JSON 报告，供人工查看或后续归档

## 报告结构

建议输出结构如下：

```json
{
  "packageRoot": "dist/OpenClaw-Portable",
  "runtimeMode": "openclaw",
  "coldRunsRequested": 3,
  "restartRunsRequested": 2,
  "summary": {
    "allPassed": true,
    "coldRunsPassed": 3,
    "restartRunsPassed": 2,
    "maxElapsedSeconds": 41.23,
    "avgElapsedSeconds": 29.44
  },
  "runs": [
    {
      "kind": "cold_start",
      "index": 1,
      "ok": true,
      "elapsedSeconds": 37.01,
      "port": 18791,
      "healthOk": true,
      "error": "",
      "stdoutLog": "C:/.../OpenClawPortable/logs/openclaw-runtime.out.log",
      "stderrLog": "C:/.../OpenClawPortable/logs/openclaw-runtime.err.log"
    }
  ]
}
```

## 架构设计

### 1. `launcher/services/runtime_stability.py`

新增一个独立服务模块，负责：

- 定义结果 dataclass
- 执行多轮冷启动 / 重启编排
- 汇总统计结果
- 把运行结果转成 JSON 友好的结构

边界：

- 不直接依赖 UI
- 不写入项目 `.context`
- 不修改 release 资产

### 2. 复用现有 runtime 适配和路径层

验证服务应复用现有：

- `PortablePaths`
- `LauncherController` 或 `OpenClawRuntimeAdapter`
- 已有健康检查和启停逻辑

关键约束是：**验证使用隔离的临时 state / temp 根目录**，不能污染包内 `state/`。这样它更接近“首启新用户”的场景，也不会让后续 release 资产被运行态文件污染。

### 3. `scripts/verify-portable-runtime-stability.py`

CLI 只负责：

- 解析参数
- 构造验证服务
- 调用验证逻辑
- 输出 JSON

建议支持参数：

- `--package-root`
- `--cold-runs`
- `--restart-runs`
- `--timeout-seconds`（可选，用于单轮等待上限）
- `--output`（可选，写 JSON 文件）

## 行为细节

### 冷启动

每轮冷启动都应：

1. 使用全新的临时 state 根目录
2. 启动 runtime
3. 等待健康检查通过
4. 记录耗时
5. 停止 runtime

这样可以模拟“全新环境首次启动”的稳定性。

### 重启

重启验证应在一轮成功启动的基础上执行：

1. 保留同一轮 state / temp 根目录
2. 调用 restart
3. 等待恢复健康
4. 记录耗时和最终端口

这样更贴近真实用户“已经配置好后重启服务”的场景。

### 失败处理

任一轮失败时：

- 该轮记录 `ok=false`
- 保留错误文案
- 记录 stdout / stderr 日志路径
- 继续还是中止：
  - 默认继续执行后续轮次，并在汇总中体现失败

原因：我们更关心“多轮里失败的分布”，而不是第一轮失败就提前退出。

## 测试策略

### 单元测试

新增 `tests/test_runtime_stability.py`，先覆盖：

- 冷启动结果汇总
- 重启结果汇总
- 失败结果保留错误信息和日志路径
- CLI 输出 JSON 结构

单测应使用 fake runner / fake adapter，不依赖真实 OpenClaw runtime。

### 手动验证

实现后再用真实 `dist/OpenClaw-Portable` 跑一轮：

```powershell
python .\scripts\verify-portable-runtime-stability.py --package-root dist\OpenClaw-Portable --cold-runs 3 --restart-runs 2
```

重点看：

- 是否能稳定输出 JSON
- 是否确实不污染包内 `state/`
- 失败时日志路径是否可用

## 验收标准

- 脚本可对指定便携包目录执行多轮稳定性验证
- 结果以结构化 JSON 输出
- 失败时保留错误与日志路径
- 单测通过
- 真实手动验证至少能跑通一轮
- 不污染发布包目录内的 `state/`
