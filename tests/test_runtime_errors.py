import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from launcher.app import OpenClawLauncherApplication
from launcher.services.runtime_errors import format_runtime_error


class RuntimeErrorMessageTests(unittest.TestCase):
    def test_missing_openclaw_runtime_message_is_user_facing(self) -> None:
        message = format_runtime_error(
            FileNotFoundError("OpenClaw runtime package not found: runtime/openclaw/package.json")
        )

        self.assertIn("缺少 OpenClaw 运行时文件", message)
        self.assertIn("prepare-openclaw-runtime.ps1", message)
        self.assertNotIn("package.json", message)

    def test_openclaw_startup_timeout_message_guides_wait_and_logs(self) -> None:
        message = format_runtime_error(TimeoutError("OpenClaw runtime did not become healthy in time"))

        self.assertIn("OpenClaw 启动时间超过预期", message)
        self.assertIn("稍等", message)
        self.assertIn("openclaw-runtime.err.log", message)

    def test_openclaw_exited_before_ready_message_mentions_logs(self) -> None:
        message = format_runtime_error(RuntimeError("OpenClaw runtime exited before becoming healthy"))

        self.assertIn("OpenClaw 启动后提前退出", message)
        self.assertIn("openclaw-runtime.err.log", message)

    def test_unknown_error_falls_back_to_original_message(self) -> None:
        message = format_runtime_error(ValueError("custom failure"))

        self.assertEqual(message, "custom failure")

    def test_application_error_boundary_uses_user_facing_runtime_message(self) -> None:
        captured_messages: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application._show_error = captured_messages.append

        def raise_missing_runtime() -> None:
            raise FileNotFoundError("OpenClaw runtime package not found: runtime/openclaw/package.json")

        application._run_with_error_boundary(raise_missing_runtime)

        self.assertEqual(len(captured_messages), 1)
        self.assertIn("缺少 OpenClaw 运行时文件", captured_messages[0])
        self.assertNotIn("package.json", captured_messages[0])


if __name__ == "__main__":
    unittest.main()
