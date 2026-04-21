from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.feishu_channel import FeishuChannelConfig, FeishuChannelService
from launcher.services.feishu_probe import build_feishu_probe_evidence, verify_feishu_channel
from launcher.services.social_channels import ChannelCommandResult


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"feishu-probe-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class FakeChannelCommandRunner:
    def __init__(self, result: ChannelCommandResult) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def run(self, args: list[str], timeout_seconds: int = 180) -> ChannelCommandResult:
        self.calls.append(args)
        return self.result


class FeishuProbeTests(unittest.TestCase):
    def test_build_feishu_probe_evidence_maps_success_payload(self) -> None:
        evidence = build_feishu_probe_evidence(
            {
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
            }
        )

        self.assertTrue(evidence.ok)
        self.assertEqual(evidence.account_id, "default")
        self.assertEqual(evidence.bot_username, "@openclaw-bot")
        self.assertEqual(evidence.last_error, "")

    def test_build_feishu_probe_evidence_maps_failure_payload(self) -> None:
        evidence = build_feishu_probe_evidence(
            {
                "channelAccounts": {
                    "feishu": [
                        {
                            "accountId": "default",
                            "enabled": True,
                            "configured": True,
                            "probe": {"ok": False},
                            "lastError": "probe failed: forbidden",
                        }
                    ]
                }
            }
        )

        self.assertFalse(evidence.ok)
        self.assertFalse(evidence.probe_ok)
        self.assertIn("forbidden", evidence.last_error)

    def test_verify_feishu_channel_requires_saved_enabled_config(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")

            with self.assertRaisesRegex(ValueError, "enabled"):
                verify_feishu_channel(paths, command_runner=FakeChannelCommandRunner(ChannelCommandResult(ok=True, output="{}")))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_verify_feishu_channel_runs_probe_command_and_returns_evidence(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            FeishuChannelService(paths).save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True))
            runner = FakeChannelCommandRunner(
                ChannelCommandResult(
                    ok=True,
                    output='{"channelAccounts":{"feishu":[{"accountId":"default","enabled":true,"configured":true,"probe":{"ok":true,"bot":{"username":"openclaw-bot"}}}]}}',
                )
            )

            evidence = verify_feishu_channel(paths, command_runner=runner)

            self.assertTrue(evidence.ok)
            self.assertEqual(runner.calls, [["channels", "status", "--probe", "--json"]])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
