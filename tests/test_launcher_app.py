import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from launcher.app import OpenClawLauncherApplication
from launcher.models import LauncherViewState


def make_view_state(status_label: str, status_detail: str, message: str) -> LauncherViewState:
    return LauncherViewState(
        status_label=status_label,
        status_detail=status_detail,
        port_label="127.0.0.1:18789",
        runtime_detail="OpenClaw gateway / v2026.4.8",
        provider_label="通义千问 / qwen-max",
        message=message,
        webui_url="http://127.0.0.1:18791",
        offline_mode=False,
    )


class FakeController:
    def __init__(self, pending_state: LauncherViewState, final_state: LauncherViewState, calls: list[str]) -> None:
        self.pending_state = pending_state
        self.final_state = final_state
        self.calls = calls

    def load_pending_runtime_view_state(self, action: str = "start") -> LauncherViewState:
        self.calls.append(f"pending:{action}")
        return self.pending_state

    def start_runtime(self) -> None:
        self.calls.append("start_runtime")

    def restart_runtime(self) -> None:
        self.calls.append("restart_runtime")

    def load_view_state(self) -> LauncherViewState:
        self.calls.append("load_view_state")
        return self.final_state

    def export_diagnostics_bundle(self) -> str:
        self.calls.append("export_diagnostics_bundle")
        return "C:/tmp/openclaw-diagnostics.zip"

    def reset_factory_state(self) -> None:
        self.calls.append("reset_factory_state")
        return True

    def import_update_package(self, package_root: Path) -> str:
        self.calls.append(f"import_update_package:{package_root}")
        return "v2026.04.2"


class FakeWindow:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.states: list[LauncherViewState] = []

    def apply_view_state(self, state: LauncherViewState) -> None:
        self.states.append(state)
        self.calls.append(f"apply:{state.status_label}")


class FakeQtApp:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def processEvents(self) -> None:
        self.calls.append("process_events")


class LauncherAppTests(unittest.TestCase):
    def test_handle_start_applies_pending_state_before_runtime_starts(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)

        application._handle_start()

        self.assertEqual(
            calls,
            ["pending:start", "apply:启动中", "process_events", "start_runtime", "load_view_state", "apply:运行中"],
        )

    def test_handle_restart_applies_pending_state_before_runtime_restarts(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("重启中", "正在重新连接本地 gateway，请稍等。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:00。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)

        application._handle_restart()

        self.assertEqual(
            calls,
            ["pending:restart", "apply:重启中", "process_events", "restart_runtime", "load_view_state", "apply:运行中"],
        )


    def test_handle_export_diagnostics_shows_success_message(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append

        application._handle_export_diagnostics()

        self.assertEqual(calls, ["export_diagnostics_bundle"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("openclaw-diagnostics.zip", info_messages[0])

    def test_handle_factory_reset_returns_to_setup_wizard_after_confirmation(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append
        application._confirm_factory_reset = lambda: True
        application.show_setup_wizard = lambda: calls.append("show_setup_wizard")

        application._handle_factory_reset()

        self.assertEqual(calls, ["reset_factory_state", "show_setup_wizard"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("已恢复到首次配置状态", info_messages[0])

    def test_handle_import_update_shows_restart_prompt_after_success(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append
        application._select_update_package_dir = lambda: "C:/tmp/update-package"

        application._handle_import_update()

        self.assertEqual(calls, ["import_update_package:C:\\tmp\\update-package"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("v2026.04.2", info_messages[0])


if __name__ == "__main__":
    unittest.main()
