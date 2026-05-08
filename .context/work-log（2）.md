# 工作日志（2）

> 续接 `work-log.md`。原文件已超过 400 行，后续工作日志先写入本文件，避免单个日志文件继续膨胀。

## 2026-05-08｜微信 ClawBot 与 release 打包链路排查收尾

- 目标：排查用户反馈的两个长时间阻塞点：微信扫码后手机端显示“暂无法连接 OpenClaw / 发消息无响应”，以及 release 打包链路反复生成后仍出现插件加载错误。
- 动作：审查并修改微信通道投影逻辑，让 QR 登录产生的真实 `accountId` 写入 `channels.openclaw-weixin.defaultAccount` 与 `channels.openclaw-weixin.accounts`；补充 `confirm_wechat_channel_login()` 后重新投影并重启 gateway 的回归测试；同时审查 release 打包脚本，发现打包产物里的 `runtime/openclaw/package.json` 曾被裁成过度精简的 shim，导致 OpenClaw 插件加载器无法解析 `dist/plugins/runtime/index.js`，于是为 `scripts/build-launcher.ps1` 增加完整 runtime manifest 保留与断言。
- 结果：源码测试和本地打包链路已有一轮修复，`dist/release/OpenClaw-Portable-v2026.05.3.zip` 已重新生成；但用户在 `2026-05-08 03:38` 复测时仍看到 `openclaw-weixin failed during register ... Unable to resolve plugin runtime module`，说明当前交付状态仍未闭环，不能宣称微信链路已修复。
- 验证：曾运行 `python -m unittest discover -s tests -v`，通过 `304` 项测试；`scripts/build-release-assets.ps1` 成功生成 release 资产；`verify-delivery-flow.py --cold-runs 1 --restart-runs 1` 的本地 package audit、release assets、runtime stability 通过，但这些验证没有覆盖“已安装 npm 外部微信插件后再次启动”的真实注册路径。
- 关键证据：用户截图显示 OpenClaw gateway 只加载 `browser, device-pair, file-transfer, memory-core, phone-control, talk-voice` 六个插件，随后 stderr 报 `openclaw-weixin failed during register ... Unable to resolve plugin runtime module`；这意味着微信插件没有注册成功，手机端扫码连接和发消息无响应都是后续表现。
- 状态：未完成。今天停止继续修复，下一次必须先复现 `state/npm/node_modules/@tencent-weixin/openclaw-weixin/dist/index.js` 的注册失败，而不是继续盲目重打包。
- 下一步：保留一个已安装微信插件的便携目录，直接运行 packaged runtime 的 `plugins list` / gateway 启动路径，确认插件加载器解析 `openclaw/plugin-sdk/*` 与 plugin runtime module 的真实规则；必要时把该路径加入自动化验证，避免 clean dist 验证通过但外部 npm 插件运行失败。

## 2026-05-08｜复现并修复微信外部 npm 插件 register 失败

- 目标：接上上一轮未闭环任务，先用保留了 `state/npm/node_modules/@tencent-weixin/openclaw-weixin` 的 packaged dist 复现 `Unable to resolve plugin runtime module`，再定位根因并固定验证入口。
- 动作：先读取 `.context/current-status.md`、`task-breakdown.md` 与本文件，确认当前优先级是微信外部 npm 插件 register 失败；随后运行定向测试确认现有补丁基线；对 `dist/OpenClaw-Portable` 设置 `OPENCLAW_CONFIG_PATH=state/runtime/openclaw.json` 后运行 `plugins list --json --verbose`，确认插件发现成功但不能证明 gateway register；接着直接启动 packaged gateway，稳定复现 stderr：`openclaw-weixin failed during register ... Unable to resolve plugin runtime module`。
- 根因：`dist/OpenClaw-Portable/runtime/openclaw/package.json` 仍是过度精简的 plugin-sdk shim（只含 `./plugin-sdk/*`），不是完整 `openclaw` manifest。OpenClaw loader 在 register 阶段需要通过 `package.json.name == "openclaw"` 定位 runtime root，进而解析 `dist/plugins/runtime/index.js`；root 定位失败后，微信插件 register 报 `Unable to resolve plugin runtime module`。
- 修复：保留并确认 `scripts/build-launcher.ps1` 的完整 manifest 复制与 `Assert-OpenClawRuntimeManifest` 防线；在当前保留现场里最小同步源码侧完整 `runtime/openclaw/package.json` 到 dist 后重跑 gateway smoke，register failure 消失。随后新增 `launcher/services/wechat_plugin_smoke.py` 与 `scripts/verify-wechat-plugin-runtime.py`，把“已安装外部 npm 微信插件后 gateway register 不失败”固化成可重复 smoke。
- 验证：`python -m unittest tests.test_wechat_plugin_smoke -v` passed 4 tests；`python -m unittest tests.test_social_channel_service tests.test_launcher_controller -v` passed 62 tests；`python scripts\verify-wechat-plugin-runtime.py --package-root dist\OpenClaw-Portable --timeout-seconds 45 --post-ready-wait-seconds 3 --output tmp\wechat-plugin-runtime-smoke.json` 返回 `ok=true`；`python -m unittest discover -s tests` passed 308 tests。
- 结果：微信外部 npm 插件 register 失败这一层已修复并有脚本防回归；真实微信联调仍未完全闭环，因为插件运行后曾出现 `weixin getUpdates error (1/3): TypeError: fetch failed`，下一步应继续验证用户网络 / 微信服务可达性 / 账号状态和真实消息收发。

## 2026-05-08｜用户确认微信修复闭环与防复发记录

- 目标：把这次终于修好的微信外部插件 register 问题记录成可执行的防复发清单，避免以后再次被 clean dist 验证误导。
- 用户反馈：用户确认“这次终于好了”，说明 `openclaw-weixin failed during register ... Unable to resolve plugin runtime module` 这一层已通过真实使用复测。
- 最终解决方法：根因不是微信扫码、账号、网络，也不是单纯的 `openclaw/plugin-sdk/*` import；根因是 packaged `runtime/openclaw/package.json` 被裁成 plugin-sdk shim，缺少 `name: openclaw` 等完整宿主 manifest 信息，导致 OpenClaw loader 无法定位 runtime root 与 `dist/plugins/runtime/index.js`。修法是在构建脚本中 prune 后复制源码侧完整 `runtime/openclaw/package.json`，并用 `Assert-OpenClawRuntimeManifest` 阻止坏包继续生成。
- 必跑防线：以后只要发包或验证微信外部 npm 插件，必须先重打包，再跑 `python scripts\verify-wechat-plugin-runtime.py --package-root dist\OpenClaw-Portable`；不能只跑 clean dist 的 delivery gate，也不能拿旧 release zip 宣称已经修好。
- 状态：已解决并经用户真实复测确认；下一步如果要交付新包，执行新版 release 资产重建和 smoke。
