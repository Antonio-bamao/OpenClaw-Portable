OpenClaw Portable / Phase 1 Development MVP

1. 双击运行 main.py（开发态）或后续打包出的 OpenClawLauncher.exe
2. 首次进入向导，完成密码、Provider、API Key 配置
3. 配置会写入 state/openclaw.json 与 state/.env
4. 主面板可启动/停止 mock runtime，并打开本地 WebUI

说明：
- 当前版本仍是开发版 MVP，运行时为 Node mock runtime
- 日志与缓存写入 %TEMP%\OpenClawPortable\
- Provider 模板位于 state/provider-templates\
