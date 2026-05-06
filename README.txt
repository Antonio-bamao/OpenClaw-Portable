OpenClaw Portable 使用说明

1. 开发态可运行 main.py；分发包中请双击 OpenClawLauncher.exe。
2. 首次进入向导，设置管理密码，并完成 Provider、API Key 配置。
3. API Key 会优先写入本地保险箱；旧配置兼容 state/.env。
4. 主面板可启动、停止真实 OpenClaw gateway，并打开本地 WebUI。
5. 没有 API Key 时可以先进入离线模式，主面板会提示补充配置。

说明：
- 日志与缓存写入 %TEMP%\OpenClawPortable\
- 用户状态保存在 state\
- 离线帮助位于 assets\guide\
- Provider 模板位于 state\provider-templates\
