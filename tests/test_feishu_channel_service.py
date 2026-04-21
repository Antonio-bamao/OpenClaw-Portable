from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from launcher.core.paths import PortablePaths
from launcher.services.feishu_channel import FeishuChannelConfig, FeishuChannelService, FeishuChannelStatus


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"feishu-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class FeishuChannelServiceTests(unittest.TestCase):
    def test_exposes_feishu_paths_from_portable_paths(self) -> None:
        paths = PortablePaths.for_root(Path("C:/tmp/OpenClaw-Portable"))

        self.assertEqual(paths.feishu_channel_dir, Path("C:/tmp/OpenClaw-Portable/state/channels/feishu"))
        self.assertEqual(paths.feishu_channel_config_file, paths.feishu_channel_dir / "config.json")
        self.assertEqual(paths.feishu_channel_status_file, paths.feishu_channel_dir / "status.json")

    def test_saves_and_loads_feishu_config_and_status(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            config = FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True, bot_app_name="OpenClaw Bot")
            status = FeishuChannelStatus(state="pending_enable", last_error="", last_connected_at=None, last_message_at=None)

            service.save_config(config)
            service.save_status(status)

            raw_config = paths.feishu_channel_config_file.read_text(encoding="utf-8")
            raw_status = paths.feishu_channel_status_file.read_text(encoding="utf-8")

            self.assertEqual(service.load_config(), config)
            self.assertEqual(service.load_status(), status)
            self.assertIn("appId", raw_config)
            self.assertIn("appSecret", raw_config)
            self.assertIn("lastError", raw_status)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_load_config_falls_back_to_default_when_json_is_invalid(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            paths.ensure_directories()
            paths.feishu_channel_config_file.write_text("{not-json", encoding="utf-8")

            service = FeishuChannelService(paths)

            self.assertEqual(service.load_config(), FeishuChannelConfig())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("launcher.services.feishu_channel.urlopen")
    def test_validate_credentials_maps_success_to_pending_enable(self, mock_urlopen) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.read.return_value = b'{"code":0,"tenant_access_token":"t-123"}'

            result = service.validate_credentials("cli_xxx", "secret")

            self.assertTrue(result.ok)
            self.assertEqual(result.state, "pending_enable")
            self.assertEqual(result.error_message, "")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_transitions_to_connected_when_runtime_reports_running(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))

            service.refresh_runtime_status(runtime_state="running", runtime_message="feishu ready")

            self.assertEqual(service.load_status().state, "connected")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_stays_pending_enable_when_runtime_cannot_open_feishu_link(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))
            service.save_status(FeishuChannelStatus(state="connection_failed", last_error="stale runtime failure"))

            service.refresh_runtime_status(
                runtime_state="ready",
                runtime_message="mock runtime ready",
                runtime_link_available=False,
            )

            self.assertEqual(service.load_status().state, "pending_enable")
            self.assertEqual(service.load_status().last_error, "")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_stays_pending_enable_when_runtime_is_ready_but_not_started(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))

            service.refresh_runtime_status(
                runtime_state="ready",
                runtime_message="runtime prepared",
            )

            self.assertEqual(service.load_status().state, "pending_enable")
            self.assertEqual(service.load_status().last_error, "")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_transitions_to_connection_failed_when_probe_reports_error(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))

            service.refresh_runtime_status(
                runtime_state="running",
                runtime_message="feishu ready",
                channel_probe_payload={
                    "channelAccounts": {
                        "feishu": [
                            {
                                "accountId": "default",
                                "enabled": True,
                                "configured": True,
                                "probe": {"ok": False},
                                "lastError": "tenant_access_token rejected",
                            }
                        ]
                    }
                },
            )

            self.assertEqual(service.load_status().state, "connection_failed")
            self.assertIn("tenant_access_token rejected", service.load_status().last_error)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_transitions_to_connected_when_probe_reports_success(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))

            service.refresh_runtime_status(
                runtime_state="running",
                runtime_message="feishu ready",
                channel_probe_payload={
                    "channelAccounts": {
                        "feishu": [
                            {
                                "accountId": "default",
                                "enabled": True,
                                "configured": True,
                                "probe": {"ok": True, "bot": {"username": "openclaw-bot"}},
                            }
                        ]
                    }
                },
            )

            self.assertEqual(service.load_status().state, "connected")
            self.assertEqual(service.load_status().last_error, "")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_status_transitions_to_connection_failed_when_probe_was_attempted_but_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))

            service.refresh_runtime_status(
                runtime_state="running",
                runtime_message="Feishu live probe did not return valid JSON.",
                probe_attempted=True,
            )

            self.assertEqual(service.load_status().state, "connection_failed")
            self.assertIn("live probe", service.load_status().last_error)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_runtime_projection_includes_default_feishu_account(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = FeishuChannelService(paths)
            config = FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True)

            projected = service.build_runtime_projection(config)

            self.assertEqual(projected.runtime_env["FEISHU_APP_ID"], "cli_xxx")
            self.assertEqual(projected.runtime_env["FEISHU_APP_SECRET"], "secret")
            self.assertTrue(projected.runtime_config_patch["channels"]["feishu"]["enabled"])
            self.assertNotIn("botAppName", projected.runtime_config_patch["channels"]["feishu"])
            self.assertEqual(projected.runtime_config_patch["channels"]["feishu"]["accounts"]["default"]["connectionMode"], "websocket")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
