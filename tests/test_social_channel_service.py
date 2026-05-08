from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.social_channels import (
    ChannelCommandResult,
    QqChannelConfig,
    SocialChannelService,
    SocialChannelStatus,
    WechatChannelConfig,
    WecomChannelConfig,
)


class FakeWechatCommandRunner:
    def __init__(self, result: ChannelCommandResult | None = None) -> None:
        self.result = result or ChannelCommandResult(ok=True)
        self.run_calls: list[list[str]] = []
        self.open_terminal_calls: list[list[str]] = []
        self.open_node_script_calls: list[Path] = []

    def run(self, args: list[str], timeout_seconds: int = 180) -> ChannelCommandResult:
        self.run_calls.append(args)
        return self.result

    def open_interactive_terminal(self, args: list[str]) -> ChannelCommandResult:
        self.open_terminal_calls.append(args)
        return self.result

    def open_node_script_terminal(self, script_path: Path) -> ChannelCommandResult:
        self.open_node_script_calls.append(script_path)
        return self.result


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"social-channels-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def mark_wechat_plugin_available(paths: PortablePaths) -> None:
    plugin_manifest = paths.state_dir / "extensions" / "openclaw-weixin" / "package.json"
    plugin_manifest.parent.mkdir(parents=True, exist_ok=True)
    plugin_manifest.write_text('{"name":"@tencent-weixin/openclaw-weixin"}\n', encoding="utf-8")
    login_entry = plugin_manifest.parent / "dist" / "src" / "auth" / "login-qr.js"
    login_entry.parent.mkdir(parents=True, exist_ok=True)
    login_entry.write_text("export {};\n", encoding="utf-8")


def mark_wechat_npm_plugin_available(paths: PortablePaths) -> None:
    plugin_root = (
        paths.state_dir
        / "npm"
        / "node_modules"
        / "@tencent-weixin"
        / "openclaw-weixin"
    )
    plugin_manifest = plugin_root / "package.json"
    plugin_manifest.parent.mkdir(parents=True, exist_ok=True)
    plugin_manifest.write_text('{"name":"@tencent-weixin/openclaw-weixin"}\n', encoding="utf-8")
    login_entry = plugin_root / "dist" / "src" / "auth" / "login-qr.js"
    login_entry.parent.mkdir(parents=True, exist_ok=True)
    login_entry.write_text("export {};\n", encoding="utf-8")


def mark_wechat_openclaw_npm_plugin_available(paths: PortablePaths) -> None:
    plugin_root = (
        paths.state_dir
        / ".openclaw"
        / "npm"
        / "node_modules"
        / "@tencent-weixin"
        / "openclaw-weixin"
    )
    plugin_manifest = plugin_root / "package.json"
    plugin_manifest.parent.mkdir(parents=True, exist_ok=True)
    plugin_manifest.write_text('{"name":"@tencent-weixin/openclaw-weixin"}\n', encoding="utf-8")
    login_entry = plugin_root / "dist" / "src" / "auth" / "login-qr.js"
    login_entry.parent.mkdir(parents=True, exist_ok=True)
    login_entry.write_text("export {};\n", encoding="utf-8")


def resolve_node_command() -> str | None:
    embedded_node = Path.cwd() / "runtime" / "node" / "node.exe"
    if embedded_node.exists():
        return str(embedded_node)
    return shutil.which("node")


class SocialChannelServiceTests(unittest.TestCase):
    def test_wechat_projection_enables_official_clawbot_plugin(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))
            config = WechatChannelConfig(enabled=True, installed=True)

            projection = service.build_wechat_runtime_projection(config)

            self.assertTrue(projection.runtime_config_patch["plugins"]["entries"]["openclaw-weixin"]["enabled"])
            self.assertTrue(projection.runtime_config_patch["channels"]["openclaw-weixin"]["enabled"])
            self.assertEqual(projection.runtime_env, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_projection_uses_qr_logged_in_account(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            account_id = "fa9e424d403c-im-bot"
            status_file = paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(
                json.dumps({"connected": True, "loggedIn": True, "accountId": account_id}),
                encoding="utf-8",
            )
            account_index = paths.state_dir / "openclaw-weixin" / "accounts.json"
            account_index.parent.mkdir(parents=True, exist_ok=True)
            account_index.write_text(json.dumps([account_id]), encoding="utf-8")
            service = SocialChannelService(paths)

            projection = service.build_wechat_runtime_projection(WechatChannelConfig(enabled=True, installed=True))
            channel = projection.runtime_config_patch["channels"]["openclaw-weixin"]

            self.assertEqual(channel["defaultAccount"], account_id)
            self.assertTrue(channel["accounts"][account_id]["enabled"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_commands_use_openclaw_weixin_install_and_qr_login(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))

            install_commands = service.wechat_install_commands()
            login_command = service.wechat_login_command()

            self.assertEqual(
                install_commands,
                [
                    ["plugins", "install", "@tencent-weixin/openclaw-weixin@latest"],
                    ["config", "set", "plugins.entries.openclaw-weixin.enabled", "true"],
                ],
            )
            self.assertEqual(login_command, ["channels", "login", "--channel", "openclaw-weixin"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_login_terminal_opens_plugin_qr_script(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runner = FakeWechatCommandRunner()
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            service = SocialChannelService(paths, command_runner=runner)
            service.save_wechat_config(WechatChannelConfig(installed=True))

            result = service.open_wechat_login_terminal()
            state = service.build_wechat_view_state()

            self.assertTrue(result.ok)
            self.assertEqual(runner.open_terminal_calls, [])
            self.assertEqual(len(runner.open_node_script_calls), 1)
            self.assertTrue(runner.open_node_script_calls[0].exists())
            script_source = runner.open_node_script_calls[0].read_text(encoding="utf-8")
            self.assertIn("startWeixinLoginWithQr", script_source)
            self.assertIn("waitForWeixinLogin", script_source)
            self.assertEqual(state.status_label, "待扫码")
            self.assertIn("二维码", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_login_script_supports_extension_imports_that_reference_openclaw_sdk(self) -> None:
        node_command = resolve_node_command()
        if not node_command:
            self.skipTest("Node.js is required to execute the generated WeChat login script.")
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            openclaw_dir = paths.runtime_dir / "openclaw"
            sdk_dir = openclaw_dir / "dist" / "plugin-sdk"
            sdk_dir.mkdir(parents=True, exist_ok=True)
            (sdk_dir / "account-id.js").write_text(
                'export function normalizeAccountId(value) { return String(value).replace("@", "-"); }\n',
                encoding="utf-8",
            )
            (sdk_dir / "infra-runtime.js").write_text(
                "export async function withFileLock(_path, _options, run) { return await run(); }\n",
                encoding="utf-8",
            )
            (sdk_dir / "config-runtime.js").write_text(
                "export async function loadConfig() { return {}; }\n"
                "export async function writeConfigFile() { return undefined; }\n",
                encoding="utf-8",
            )
            plugin_root = paths.state_dir / "extensions" / "openclaw-weixin"
            auth_dir = plugin_root / "dist" / "src" / "auth"
            auth_dir.mkdir(parents=True, exist_ok=True)
            (plugin_root / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
            (auth_dir / "login-qr.js").write_text(
                """
export const DEFAULT_ILINK_BOT_TYPE = "3";
export async function startWeixinLoginWithQr() {
  return { qrcodeUrl: "https://example.test/qr", sessionKey: "session", message: "qr" };
}
export async function displayQRCode() {}
export async function waitForWeixinLogin() {
  return { connected: true, botToken: "token", accountId: "abc@im.bot", baseUrl: "https://api.example.test", userId: "user" };
}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (auth_dir / "accounts.js").write_text(
                """
import { normalizeAccountId } from "openclaw/plugin-sdk/account-id";
import { registerUserInFrameworkStore } from "./pairing.js";
export function saveWeixinAccount(accountId) {
  if (normalizeAccountId(accountId) !== accountId) throw new Error("account was not normalized");
}
export async function registerWeixinAccountId(accountId) { await registerUserInFrameworkStore({ accountId, userId: "user" }); }
export function clearStaleAccountsForUserId() {}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (auth_dir / "pairing.js").write_text(
                """
import fs from "node:fs";
import { withFileLock } from "openclaw/plugin-sdk/infra-runtime";
export async function registerUserInFrameworkStore(params) {
  return await withFileLock("demo.lock", {}, async () => {
    fs.writeFileSync("allow-from-called.txt", JSON.stringify(params), "utf-8");
    return { changed: Boolean(params.accountId && params.userId) };
  });
}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            service = SocialChannelService(paths)
            script_path = service._write_wechat_login_script()

            completed = subprocess.run(
                [node_command, str(script_path)],
                cwd=str(openclaw_dir),
                env={**os.environ, "OPENCLAW_STATE_DIR": str(paths.state_dir), "OPENCLAW_HOME": str(paths.state_dir)},
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            status = json.loads((paths.state_dir / "channels" / "openclaw-weixin" / "status.json").read_text(encoding="utf-8"))
            self.assertTrue(status["connected"])
            self.assertEqual(status["accountId"], "abc-im.bot")
            allow_from_call = json.loads((openclaw_dir / "allow-from-called.txt").read_text(encoding="utf-8"))
            self.assertEqual(allow_from_call["accountId"], "abc-im.bot")
            self.assertEqual(allow_from_call["userId"], "user")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_login_refuses_stale_installed_state_when_plugin_is_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runner = FakeWechatCommandRunner()
            service = SocialChannelService(make_paths(temp_dir), command_runner=runner)
            service.save_wechat_config(WechatChannelConfig(installed=True))
            service.save_wechat_status(SocialChannelStatus(state="pending_login"))

            result = service.open_wechat_login_terminal()
            state = service.build_wechat_view_state()

            self.assertFalse(result.ok)
            self.assertEqual(runner.open_terminal_calls, [])
            self.assertEqual(runner.open_node_script_calls, [])
            self.assertFalse(service.load_wechat_config().installed)
            self.assertEqual(state.status_label, "未安装")
            self.assertIn("重新安装", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_pending_login_status_message_does_not_mark_login_failed(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            service = SocialChannelService(paths)
            service.save_wechat_config(WechatChannelConfig(installed=True))
            service.save_wechat_status(SocialChannelStatus(state="pending_login"))
            status_file = paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(
                json.dumps({"connected": False, "state": "pending_login", "message": "等待扫码确认。"}),
                encoding="utf-8",
            )

            service.confirm_wechat_runtime_login()
            state = service.build_wechat_view_state()

            self.assertEqual(state.status_label, "待扫码")
            self.assertNotEqual(service.load_wechat_status().state, "login_failed")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_runtime_plugin_available_detects_openclaw_npm_install(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_openclaw_npm_plugin_available(paths)
            service = SocialChannelService(paths)

            self.assertTrue(service.wechat_runtime_plugin_available())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_runtime_plugin_available_detects_state_npm_install(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_npm_plugin_available(paths)
            service = SocialChannelService(paths)

            self.assertTrue(service.wechat_runtime_plugin_available())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_view_state_recovers_stale_missing_status_when_plugin_exists(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_npm_plugin_available(paths)
            service = SocialChannelService(paths)
            service.save_wechat_config(WechatChannelConfig(installed=False, enabled=False))
            service.save_wechat_status(
                SocialChannelStatus(
                    state="missing_runtime_plugin",
                    last_error="未找到微信插件文件，请重新安装微信 ClawBot 通道插件。",
                )
            )

            state = service.build_wechat_view_state()

            self.assertTrue(state.installed)
            self.assertEqual(state.status_label, "待扫码")
            self.assertTrue(service.load_wechat_config().installed)
            self.assertEqual(service.load_wechat_status().state, "pending_login")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_install_failure_surfaces_error_after_visible_installing_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runner = FakeWechatCommandRunner(ChannelCommandResult(ok=False, error_message="Cannot find module zod"))
            service = SocialChannelService(make_paths(temp_dir), command_runner=runner)

            result = service.install_wechat_plugin()
            state = service.build_wechat_view_state()

            self.assertFalse(result.ok)
            self.assertEqual(state.status_label, "安装失败")
            self.assertIn("Cannot find module zod", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_install_is_idempotent_when_extension_already_exists(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            stale_stage = paths.state_dir / "extensions" / ".openclaw-install-stage-old" / "index.ts"
            stale_stage.parent.mkdir(parents=True, exist_ok=True)
            stale_stage.write_text("export default {}\n", encoding="utf-8")
            runner = FakeWechatCommandRunner(ChannelCommandResult(ok=False, error_message="plugin already exists"))
            service = SocialChannelService(paths, command_runner=runner)

            result = service.install_wechat_plugin()
            state = service.build_wechat_view_state()

            self.assertTrue(result.ok)
            self.assertEqual(runner.run_calls, [])
            self.assertTrue(service.load_wechat_config().installed)
            self.assertEqual(state.status_label, "待扫码")
            self.assertFalse(stale_stage.parent.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wecom_install_is_idempotent_when_extension_already_exists(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            installed_plugin = paths.state_dir / "extensions" / "wecom-openclaw-plugin" / "package.json"
            installed_plugin.parent.mkdir(parents=True, exist_ok=True)
            installed_plugin.write_text('{"name":"@wecom/wecom-openclaw-plugin"}\n', encoding="utf-8")
            runner = FakeWechatCommandRunner(ChannelCommandResult(ok=False, error_message="plugin already exists"))
            service = SocialChannelService(paths, command_runner=runner)

            result = service.install_wecom_plugin()
            state = service.build_wecom_view_state()

            self.assertTrue(result.ok)
            self.assertEqual(runner.run_calls, [])
            self.assertEqual(state.status_label, "待配置")
            self.assertIn("已安装", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_qq_projection_uses_bundled_qqbot_app_credentials(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))
            config = QqChannelConfig(app_id="123456", app_secret="secret", enabled=True)

            projection = service.build_qq_runtime_projection(config)

            qqbot = projection.runtime_config_patch["channels"]["qqbot"]
            self.assertTrue(qqbot["enabled"])
            self.assertEqual(qqbot["appId"], "123456")
            self.assertEqual(qqbot["clientSecret"], "secret")
            self.assertTrue(qqbot["accounts"]["default"]["enabled"])
            self.assertEqual(projection.runtime_env["QQBOT_APP_ID"], "123456")
            self.assertEqual(projection.runtime_env["QQBOT_CLIENT_SECRET"], "secret")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_qq_onboarding_command_uses_documented_token_format(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))

            command = service.qq_onboarding_command(QqChannelConfig(app_id=" 123456 ", app_secret=" secret "))

            self.assertEqual(
                command,
                ["channels", "add", "--channel", "qqbot", "--token", "123456:secret"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_qq_validation_rejects_package_when_bundled_extension_is_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            (paths.runtime_dir / "openclaw").mkdir(parents=True)
            service = SocialChannelService(paths)

            result = service.validate_qq_config(QqChannelConfig(app_id="123456", app_secret="secret"))

            self.assertFalse(result.ok)
            self.assertEqual(result.state, "missing_runtime_plugin")
            self.assertIn("QQ Bot", result.error_message)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wechat_refresh_marks_pending_enable_when_runtime_reports_logged_in(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            service = SocialChannelService(paths)
            service.save_wechat_config(WechatChannelConfig(installed=True))
            status_file = paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(json.dumps({"loggedIn": True, "lastLoginAt": "2026-04-17T10:00:00Z"}), encoding="utf-8")

            service.refresh_wechat_runtime_status()
            state = service.build_wechat_view_state()

            self.assertEqual(state.last_login_at, "2026-04-17T10:00:00Z")
            self.assertIn("启用", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_confirm_wechat_runtime_login_refreshes_state_immediately(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            service = SocialChannelService(paths)
            service.save_wechat_config(WechatChannelConfig(installed=True))
            status_file = paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(json.dumps({"connected": True, "lastLoginAt": "2026-04-18T08:00:00Z"}), encoding="utf-8")

            service.confirm_wechat_runtime_login()
            state = service.build_wechat_view_state()

            self.assertEqual(state.last_login_at, "2026-04-18T08:00:00Z")
            self.assertIn("启用", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_confirm_wechat_runtime_login_surfaces_runtime_login_failure(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            mark_wechat_plugin_available(paths)
            service = SocialChannelService(paths)
            service.save_wechat_config(WechatChannelConfig(installed=True))
            status_file = paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(
                json.dumps({"connected": False, "state": "login_failed", "lastError": "二维码已过期"}),
                encoding="utf-8",
            )

            service.confirm_wechat_runtime_login()
            state = service.build_wechat_view_state()

            self.assertEqual(state.status_label, "扫码失败")
            self.assertIn("二维码已过期", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_qq_view_state_surfaces_missing_runtime_plugin_message(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            service = SocialChannelService(paths)
            service.save_qq_config(QqChannelConfig(app_id="123456", app_secret="secret"))
            service.save_qq_status(
                service.load_qq_status().__class__(
                    state="missing_runtime_plugin",
                    last_error="当前便携包缺少内置 QQ Bot 扩展，请重新安装或更新 OpenClaw Portable。",
                )
            )

            state = service.build_qq_view_state()

            self.assertEqual(state.status_label, "缺少扩展")
            self.assertIn("QQ Bot", state.status_detail)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_wecom_projection_and_install_command_use_wecom_plugin(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))
            config = WecomChannelConfig(bot_id="wwbot", secret="secret", enabled=True)

            projection = service.build_wecom_runtime_projection(config)

            wecom = projection.runtime_config_patch["channels"]["wecom"]
            self.assertTrue(wecom["enabled"])
            self.assertEqual(wecom["botId"], "wwbot")
            self.assertEqual(wecom["secret"], "secret")
            self.assertEqual(wecom["connectionMode"], "websocket")
            self.assertEqual(service.wecom_install_commands(), [["plugins", "install", "@wecom/wecom-openclaw-plugin@latest"]])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_saves_and_loads_social_channel_configs(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = SocialChannelService(make_paths(temp_dir))

            service.save_qq_config(QqChannelConfig(app_id="123456", app_secret="secret", enabled=True))
            service.save_wecom_config(WecomChannelConfig(bot_id="wwbot", secret="secret", enabled=True))
            service.save_wechat_config(WechatChannelConfig(enabled=True, installed=True))

            self.assertEqual(service.load_qq_config().app_id, "123456")
            self.assertEqual(service.load_wecom_config().bot_id, "wwbot")
            self.assertTrue(service.load_wechat_config().installed)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
