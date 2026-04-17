from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.social_channels import (
    ChannelCommandResult,
    QqChannelConfig,
    SocialChannelService,
    WechatChannelConfig,
    WecomChannelConfig,
)


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"social-channels-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


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
