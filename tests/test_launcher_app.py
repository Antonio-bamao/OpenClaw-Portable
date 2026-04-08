import os
import unittest

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
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-60 秒。", "请勿关闭窗口。")
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


if __name__ == "__main__":
    unittest.main()
