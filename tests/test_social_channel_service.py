from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.social_channels import (
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
            self.assertEqual(projection.runtime_env, {})
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
