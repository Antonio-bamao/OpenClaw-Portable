import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from launcher.app import OpenClawLauncherApplication
from launcher.models import FeishuChannelState, LauncherViewState, QqChannelState, WechatChannelState, WecomChannelState
from launcher.services.window_preferences import CloseAction, WindowPreferenceStore


def make_view_state(status_label: str, status_detail: str, message: str, *, offline_mode: bool = False) -> LauncherViewState:
    return LauncherViewState(
        status_label=status_label,
        status_detail=status_detail,
        port_label="127.0.0.1:18789",
        runtime_detail="OpenClaw gateway / v2026.4.8",
        provider_label="通义千问 / qwen-max",
        message=message,
        webui_url="http://127.0.0.1:18789/#token=uclaw",
        offline_mode=offline_mode,
    )


class FakeController:
    def __init__(self, pending_state: LauncherViewState, final_state: LauncherViewState, calls: list[str]) -> None:
        self.pending_state = pending_state
        self.final_state = final_state
        self.calls = calls
        self.update_check_result = type(
            "UpdateCheckResult",
            (),
            {
                "update_available": True,
                "latest_version": "v2026.04.2",
                "notes": ["升级到新的 OpenClaw runtime"],
                "package_url": "https://example.com/pkg.zip",
            },
        )()

    def load_pending_runtime_view_state(self, action: str = "start") -> LauncherViewState:
        self.calls.append(f"pending:{action}")
        return self.pending_state

    def start_runtime(self) -> None:
        self.calls.append("start_runtime")

    def restart_runtime(self) -> None:
        self.calls.append("restart_runtime")

    def stop_runtime(self) -> None:
        self.calls.append("stop_runtime")

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

    def restore_update_backup(self, backup_root: Path) -> str:
        self.calls.append(f"restore_update_backup:{backup_root}")
        return "v2026.03.9"

    def check_for_updates(self):
        self.calls.append("check_for_updates")
        return self.update_check_result

    def download_and_import_update(self, metadata) -> str:
        self.calls.append(f"download_and_import_update:{metadata.latest_version}")
        return metadata.latest_version

    def save_feishu_channel(self, app_id: str, app_secret: str, bot_app_name: str) -> FeishuChannelState:
        self.calls.append(f"save_feishu_channel:{app_id}:{app_secret}:{bot_app_name}")
        return FeishuChannelState(
            app_id=app_id,
            app_secret=app_secret,
            bot_app_name=bot_app_name,
            enabled=False,
            status_label="待启用",
            status_detail="saved",
        )

    def test_feishu_channel(self) -> FeishuChannelState:
        self.calls.append("test_feishu_channel")
        return FeishuChannelState("cli_xxx", "secret", "Support Bot", False, "待启用", "tested")

    def enable_feishu_channel(self) -> FeishuChannelState:
        self.calls.append("enable_feishu_channel")
        return FeishuChannelState("cli_xxx", "secret", "Support Bot", True, "连接中", "enabled")

    def disable_feishu_channel(self) -> FeishuChannelState:
        self.calls.append("disable_feishu_channel")
        return FeishuChannelState("cli_xxx", "secret", "Support Bot", False, "待启用", "disabled")

    def should_auto_start_runtime(self) -> bool:
        self.calls.append("should_auto_start_runtime")
        return True


    def install_wechat_channel(self) -> WechatChannelState:
        self.calls.append("install_wechat_channel")
        return WechatChannelState(False, True, "待扫码", "installed")

    def login_wechat_channel(self) -> WechatChannelState:
        self.calls.append("login_wechat_channel")
        return WechatChannelState(False, True, "待启用", "login opened")

    def confirm_wechat_channel_login(self) -> WechatChannelState:
        self.calls.append("confirm_wechat_channel_login")
        return WechatChannelState(False, True, "待启用", "confirmed")

    def enable_wechat_channel(self) -> WechatChannelState:
        self.calls.append("enable_wechat_channel")
        return WechatChannelState(True, True, "已启用", "enabled")

    def disable_wechat_channel(self) -> WechatChannelState:
        self.calls.append("disable_wechat_channel")
        return WechatChannelState(False, True, "待启用", "disabled")

    def save_qq_channel(self, app_id: str, app_secret: str) -> QqChannelState:
        self.calls.append(f"save_qq_channel:{app_id}:{app_secret}")
        return QqChannelState(app_id, app_secret, False, "待启用", "saved")

    def test_qq_channel(self) -> QqChannelState:
        self.calls.append("test_qq_channel")
        return QqChannelState("123456", "secret", False, "待启用", "tested")

    def enable_qq_channel(self) -> QqChannelState:
        self.calls.append("enable_qq_channel")
        return QqChannelState("123456", "secret", True, "已启用", "enabled")

    def disable_qq_channel(self) -> QqChannelState:
        self.calls.append("disable_qq_channel")
        return QqChannelState("123456", "secret", False, "待启用", "disabled")

    def install_wecom_channel(self) -> WecomChannelState:
        self.calls.append("install_wecom_channel")
        return WecomChannelState("", "", False, "websocket", "待配置", "installed")

    def save_wecom_channel(self, bot_id: str, secret: str) -> WecomChannelState:
        self.calls.append(f"save_wecom_channel:{bot_id}:{secret}")
        return WecomChannelState(bot_id, secret, False, "websocket", "待启用", "saved")

    def test_wecom_channel(self) -> WecomChannelState:
        self.calls.append("test_wecom_channel")
        return WecomChannelState("wwbot", "secret", False, "websocket", "待启用", "tested")

    def enable_wecom_channel(self) -> WecomChannelState:
        self.calls.append("enable_wecom_channel")
        return WecomChannelState("wwbot", "secret", True, "websocket", "已启用", "enabled")

    def disable_wecom_channel(self) -> WecomChannelState:
        self.calls.append("disable_wecom_channel")
        return WecomChannelState("wwbot", "secret", False, "websocket", "待启用", "disabled")


class FakeInput:
    def __init__(self, value: str) -> None:
        self.value = value

    def text(self) -> str:
        return self.value


class FakeWindow:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.states: list[LauncherViewState] = []
        self.feishu_states: list[FeishuChannelState] = []
        self.wechat_states: list[WechatChannelState] = []
        self.qq_states: list[QqChannelState] = []
        self.wecom_states: list[WecomChannelState] = []
        self.busy_actions: list[tuple[str, bool]] = []
        self.console_snapshots: list[tuple[str, str]] = []
        self.feishu_app_id_input = FakeInput("cli_xxx")
        self.feishu_app_secret_input = FakeInput("secret")
        self.feishu_bot_name_input = FakeInput("Support Bot")
        self.qq_app_id_input = FakeInput("123456")
        self.qq_app_secret_input = FakeInput("qq-secret")
        self.wecom_bot_id_input = FakeInput("wwbot")
        self.wecom_secret_input = FakeInput("wecom-secret")

    def hide(self) -> None:
        self.calls.append("hide_window")

    def show(self) -> None:
        self.calls.append("show_window")

    def raise_(self) -> None:
        self.calls.append("raise_window")

    def activateWindow(self) -> None:
        self.calls.append("activate_window")

    def apply_view_state(self, state: LauncherViewState) -> None:
        self.states.append(state)
        self.calls.append(f"apply:{state.status_label}")

    def set_action_busy(self, action: str, busy: bool) -> None:
        self.busy_actions.append((action, busy))
        self.calls.append(f"busy:{action}:{busy}")

    def apply_feishu_channel_state(self, state: FeishuChannelState) -> None:
        self.feishu_states.append(state)
        self.calls.append(f"apply_feishu:{state.status_label}")

    def apply_wechat_channel_state(self, state: WechatChannelState) -> None:
        self.wechat_states.append(state)
        self.calls.append(f"apply_wechat:{state.status_label}")

    def apply_qq_channel_state(self, state: QqChannelState) -> None:
        self.qq_states.append(state)
        self.calls.append(f"apply_qq:{state.status_label}")

    def apply_wecom_channel_state(self, state: WecomChannelState) -> None:
        self.wecom_states.append(state)
        self.calls.append(f"apply_wecom:{state.status_label}")

    def apply_runtime_console(self, status: str, output: str) -> None:
        self.console_snapshots.append((status, output))
        self.calls.append(f"console:{status}")


class FakeQtApp:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def processEvents(self) -> None:
        self.calls.append("process_events")

    def quit(self) -> None:
        self.calls.append("app_quit")


class LauncherAppTests(unittest.TestCase):
    def test_default_project_root_uses_module_root_in_source_mode(self) -> None:
        project_root = OpenClawLauncherApplication._default_project_root()

        self.assertEqual(project_root, Path(__file__).resolve().parent.parent)

    def test_default_project_root_uses_executable_directory_when_frozen(self) -> None:
        fake_executable = Path("C:/Portable/OpenClaw-Portable/OpenClawLauncher.exe")

        with patch("launcher.app.sys", frozen=True, executable=str(fake_executable)):
            project_root = OpenClawLauncherApplication._default_project_root()

        self.assertEqual(project_root, fake_executable.parent)

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
            [
                "pending:start",
                "apply:启动中",
                "process_events",
                "start_runtime",
                "load_view_state",
                "apply:运行中",
                "console:Gateway 已就绪，飞书已连接",
            ],
        )

    def test_handle_start_ignores_duplicate_click_while_busy(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._busy_actions = {"start_runtime"}

        application._handle_start()

        self.assertNotIn("start_runtime", calls)

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
            [
                "pending:restart",
                "apply:重启中",
                "process_events",
                "restart_runtime",
                "load_view_state",
                "apply:运行中",
                "console:Gateway 已就绪，飞书已连接",
            ],
        )

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_auto_start_starts_runtime_and_opens_dashboard(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._auto_start_attempted = False
        application._auto_opened_webui = False

        application._auto_start_runtime()

        self.assertEqual(
            calls,
            [
                "should_auto_start_runtime",
                "pending:start",
                "apply:启动中",
                "process_events",
                "start_runtime",
                "load_view_state",
                "apply:运行中",
                "console:Gateway 已就绪，飞书已连接",
                "load_view_state",
            ],
        )
        mock_open_new_tab.assert_called_once_with("http://127.0.0.1:18789/#token=uclaw")

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_auto_start_keeps_main_window_when_api_key_is_missing(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state(
            "运行中",
            "本地运行时正在响应请求，已运行 00:01。",
            "通义千问 的 API Key 尚未配置。",
            offline_mode=True,
        )
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._auto_start_attempted = False
        application._auto_opened_webui = False
        application.show_setup_wizard = lambda: calls.append("show_setup_wizard")

        application._auto_start_runtime()

        self.assertNotIn("show_setup_wizard", calls)
        self.assertEqual(
            calls,
            [
                "should_auto_start_runtime",
                "pending:start",
                "apply:启动中",
                "process_events",
                "start_runtime",
                "load_view_state",
                "apply:运行中",
                "console:Gateway 已就绪，飞书已连接",
                "load_view_state",
            ],
        )
        mock_open_new_tab.assert_not_called()

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_auto_start_runs_only_once(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(
            make_view_state("启动中", "pending", ""),
            make_view_state("运行中", "running", "ready"),
            calls,
        )
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._auto_start_attempted = True
        application._auto_opened_webui = False

        application._auto_start_runtime()

        self.assertEqual(calls, [])
        mock_open_new_tab.assert_not_called()


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

    def test_handle_restore_update_backup_shows_restart_prompt_after_success(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append
        application._confirm_restore_update_backup = lambda: True
        application._select_update_backup_dir = lambda: "C:/tmp/update-backup"

        application._handle_restore_update_backup()

        self.assertEqual(calls, ["restore_update_backup:C:\\tmp\\update-backup"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("v2026.03.9", info_messages[0])

    def test_handle_check_update_shows_latest_message_when_no_update_is_available(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        controller = FakeController(pending_state, final_state, calls)
        controller.update_check_result = type(
            "UpdateCheckResult",
            (),
            {"update_available": False, "latest_version": "v2026.04.1", "notes": [], "package_url": ""},
        )()
        application.controller = controller
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append

        application._handle_check_update()

        self.assertEqual(calls, ["check_for_updates"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("最新版本", info_messages[0])

    def test_handle_check_update_downloads_and_imports_after_confirmation(self) -> None:
        calls: list[str] = []
        info_messages: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._show_info = info_messages.append
        application._confirm_online_update = lambda metadata: True

        application._handle_check_update()

        self.assertEqual(calls, ["check_for_updates", "download_and_import_update:v2026.04.2"])
        self.assertEqual(len(info_messages), 1)
        self.assertIn("v2026.04.2", info_messages[0])

    def test_handle_check_update_ignores_duplicate_click_while_busy(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。", "请勿关闭窗口。")
        final_state = make_view_state("运行中", "本地运行时正在响应请求，已运行 00:01。", "当前正在使用真实 OpenClaw gateway。")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application._busy_actions = {"check_update"}
        application._confirm_online_update = lambda metadata: False

        application._handle_check_update()

        self.assertNotIn("check_for_updates", calls)

    def test_close_request_minimizes_to_tray_without_stopping_runtime(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application.close_preferences = type("Prefs", (), {"load_close_action": lambda self: CloseAction.ASK})()
        application._ask_close_action = lambda: (CloseAction.MINIMIZE_TO_TRAY, False)
        application._show_tray_message = lambda: calls.append("tray_message")

        should_close = application._handle_main_window_close_request()

        self.assertFalse(should_close)
        self.assertIn("hide_window", calls)
        self.assertIn("tray_message", calls)
        self.assertNotIn("stop_runtime", calls)
        self.assertNotIn("app_quit", calls)

    def test_close_request_full_exit_stops_runtime_before_quitting(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application.close_preferences = type("Prefs", (), {"load_close_action": lambda self: CloseAction.ASK})()
        application._ask_close_action = lambda: (CloseAction.EXIT, False)

        should_close = application._handle_main_window_close_request()

        self.assertTrue(should_close)
        self.assertLess(calls.index("stop_runtime"), calls.index("app_quit"))

    def test_close_request_can_remember_minimize_to_tray(self) -> None:
        calls: list[str] = []

        class FakePreferences:
            def __init__(self) -> None:
                self.saved: list[CloseAction] = []

            def load_close_action(self) -> CloseAction:
                return CloseAction.ASK

            def save_close_action(self, action: CloseAction) -> None:
                self.saved.append(action)

        preferences = FakePreferences()
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application.close_preferences = preferences
        application._ask_close_action = lambda: (CloseAction.MINIMIZE_TO_TRAY, True)
        application._show_tray_message = lambda: None

        should_close = application._handle_main_window_close_request()

        self.assertFalse(should_close)
        self.assertEqual(preferences.saved, [CloseAction.MINIMIZE_TO_TRAY])

    def test_remembered_minimize_to_tray_skips_close_prompt(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.app = FakeQtApp(calls)
        application.close_preferences = type("Prefs", (), {"load_close_action": lambda self: CloseAction.MINIMIZE_TO_TRAY})()
        application._ask_close_action = lambda: (_ for _ in ()).throw(AssertionError("prompt should not be shown"))
        application._show_tray_message = lambda: calls.append("tray_message")

        should_close = application._handle_main_window_close_request()

        self.assertFalse(should_close)
        self.assertIn("hide_window", calls)

    def test_window_close_preference_store_persists_remembered_action(self) -> None:
        temp_dir = Path.cwd() / "tmp" / "window-preferences-test"
        try:
            store = WindowPreferenceStore(temp_dir)

            self.assertEqual(store.load_close_action(), CloseAction.ASK)

            store.save_close_action(CloseAction.MINIMIZE_TO_TRAY)

            self.assertEqual(WindowPreferenceStore(temp_dir).load_close_action(), CloseAction.MINIMIZE_TO_TRAY)
        finally:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)


    def test_handle_save_feishu_channel_reads_inputs_and_applies_state(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "pending", "please wait")
        final_state = make_view_state("运行中", "running", "ready")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)

        application._handle_save_feishu_channel()

        self.assertIn("save_feishu_channel:cli_xxx:secret:Support Bot", calls)
        self.assertEqual(application.main_window.feishu_states[-1].status_label, "待启用")

    def test_handle_enable_feishu_channel_applies_enabled_state(self) -> None:
        calls: list[str] = []
        pending_state = make_view_state("启动中", "pending", "please wait")
        final_state = make_view_state("运行中", "running", "ready")
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(pending_state, final_state, calls)
        application.main_window = FakeWindow(calls)

        application._handle_enable_feishu_channel()

        self.assertIn("enable_feishu_channel", calls)
        self.assertEqual(application.main_window.feishu_states[-1].status_label, "连接中")

    def test_refresh_runtime_console_applies_live_log_summary_and_tail(self) -> None:
        temp_dir = Path.cwd() / "tmp" / "runtime-console-test"
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        try:
            (logs_dir / "openclaw-runtime.out.log").write_text(
                "[gateway] ready\n[feishu] feishu[default]: WebSocket client started\n[info]: [ '[ws]', 'ws client ready' ]\n",
                encoding="utf-8",
            )
            (logs_dir / "openclaw-runtime.err.log").write_text("", encoding="utf-8")

            calls: list[str] = []
            application = object.__new__(OpenClawLauncherApplication)
            application.paths = type("Paths", (), {"logs_dir": logs_dir})()
            application.main_window = FakeWindow(calls)

            application._refresh_runtime_console()

            summary, output = application.main_window.console_snapshots[-1]
            self.assertIn("Gateway 已就绪", summary)
            self.assertIn("飞书已连接", summary)
            self.assertIn("[gateway] ready", output)
        finally:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

    def test_poll_runtime_state_refreshes_view_and_console(self) -> None:
        temp_dir = Path.cwd() / "tmp" / "runtime-poll-test"
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        try:
            (logs_dir / "openclaw-runtime.out.log").write_text("[gateway] starting...\n", encoding="utf-8")
            (logs_dir / "openclaw-runtime.err.log").write_text("", encoding="utf-8")

            calls: list[str] = []
            application = object.__new__(OpenClawLauncherApplication)
            application.paths = type("Paths", (), {"logs_dir": logs_dir})()
            application.controller = FakeController(
                make_view_state("启动中", "pending", "please wait"),
                make_view_state("运行中", "running", "ready"),
                calls,
            )
            application.main_window = FakeWindow(calls)

            application._poll_runtime_state()

            self.assertIn("load_view_state", calls)
            self.assertIn("apply:运行中", calls)
            self.assertTrue(any(call.startswith("console:") for call in calls))
        finally:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)


    def test_handle_wechat_install_login_and_enable_apply_states(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)

        application._handle_install_wechat_channel()
        application._handle_login_wechat_channel()
        application._handle_enable_wechat_channel()

        self.assertIn("install_wechat_channel", calls)
        self.assertIn("login_wechat_channel", calls)
        self.assertIn("enable_wechat_channel", calls)
        self.assertEqual(application.main_window.wechat_states[-1].status_label, "已启用")

    def test_handle_confirm_wechat_channel_refreshes_state(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)

        application._handle_confirm_wechat_channel()

        self.assertIn("confirm_wechat_channel_login", calls)
        self.assertEqual(application.main_window.wechat_states[-1].status_detail, "confirmed")

    def test_handle_save_and_enable_qq_channel_reads_inputs(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)

        application._handle_save_qq_channel()
        application._handle_enable_qq_channel()

        self.assertIn("save_qq_channel:123456:qq-secret", calls)
        self.assertIn("enable_qq_channel", calls)
        self.assertEqual(application.main_window.qq_states[-1].status_label, "已启用")

    def test_handle_save_and_enable_wecom_channel_reads_inputs(self) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)

        application._handle_install_wecom_channel()
        application._handle_save_wecom_channel()
        application._handle_enable_wecom_channel()

        self.assertIn("install_wecom_channel", calls)
        self.assertIn("save_wecom_channel:wwbot:wecom-secret", calls)
        self.assertIn("enable_wecom_channel", calls)
        self.assertEqual(application.main_window.wecom_states[-1].status_label, "已启用")

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_handle_open_webui_opens_runtime_gateway_dashboard_url(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(
            make_view_state("启动中", "pending", "please wait"),
            make_view_state("运行中", "running", "ready"),
            calls,
        )
        application.main_window = FakeWindow(calls)
        application.wizard_window = None

        application._handle_open_webui()

        mock_open_new_tab.assert_called_once_with("http://127.0.0.1:18789/#token=uclaw")
        self.assertEqual(calls, ["load_view_state"])

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_handle_open_wechat_help_opens_packaged_help_page(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.wizard_window = None
        application.paths = type("Paths", (), {"assets_dir": Path.cwd() / "assets"})()

        application._handle_open_wechat_help()

        mock_open_new_tab.assert_called_once()
        self.assertIn("setup-wechat.html", mock_open_new_tab.call_args.args[0])

    @patch("launcher.app.webbrowser.open_new_tab")
    def test_handle_open_qq_help_opens_packaged_help_page(self, mock_open_new_tab) -> None:
        calls: list[str] = []
        application = object.__new__(OpenClawLauncherApplication)
        application.controller = FakeController(make_view_state("pending", "pending", ""), make_view_state("running", "running", ""), calls)
        application.main_window = FakeWindow(calls)
        application.wizard_window = None
        application.paths = type("Paths", (), {"assets_dir": Path.cwd() / "assets"})()

        application._handle_open_qq_help()

        mock_open_new_tab.assert_called_once()
        self.assertIn("setup-qq.html", mock_open_new_tab.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
