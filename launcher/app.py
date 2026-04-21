from __future__ import annotations

import sys
import webbrowser
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from launcher.bootstrap import AppRoute, LauncherBootstrap
from launcher.core.paths import PortablePaths
from launcher.services.controller import LauncherController
from launcher.services.provider_registry import ProviderTemplateRegistry
from launcher.services.runtime_errors import format_runtime_error
from launcher.services.runtime_mode import resolve_runtime_mode
from launcher.services.online_update import UpdateCheckResult
from launcher.ui.main_window import OpenClawLauncherWindow
from launcher.ui.theme import preferred_font
from launcher.ui.wizard import SetupWizardWindow


class BackgroundTaskSignals(QObject):
    completed = Signal(str, object, object, bool)


class OpenClawLauncherApplication:
    def __init__(self, project_root: Path | None = None, node_command: str = "node", runtime_mode: str | None = None) -> None:
        self.project_root = project_root or self._default_project_root()
        self.paths = PortablePaths.for_root(self.project_root)
        selected_runtime_mode = resolve_runtime_mode(self.paths, requested_mode=runtime_mode)
        self.controller = LauncherController(self.paths, node_command=node_command, runtime_mode=selected_runtime_mode)
        self.registry = ProviderTemplateRegistry(self.paths.provider_templates_dir)
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setFont(preferred_font())
        self.main_window: OpenClawLauncherWindow | None = None
        self.wizard_window: SetupWizardWindow | None = None
        self._busy_actions: set[str] = set()
        self._background_executor = ThreadPoolExecutor(max_workers=1)
        self._background_signals = BackgroundTaskSignals()
        self._background_signals.completed.connect(self._finish_background_action)
        self._runtime_poll_timer = QTimer()
        self._runtime_poll_timer.setInterval(1000)
        self._runtime_poll_timer.timeout.connect(self._poll_runtime_state)
        self.app.aboutToQuit.connect(self._shutdown_background_executor)

    @staticmethod
    def _default_project_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent

    def run(self) -> int:
        route = LauncherBootstrap(self.paths).initial_route()
        if route == AppRoute.SETUP_WIZARD:
            self.show_setup_wizard()
        else:
            self.show_main_window()
        return self.app.exec()

    def show_main_window(self) -> None:
        view_state = self.controller.load_view_state()
        if not self.main_window:
            self.main_window = OpenClawLauncherWindow(view_state)
            self.main_window.bind_handlers(
                on_start=self._handle_start,
                on_stop=self._handle_stop,
                on_restart=self._handle_restart,
                on_open_webui=self._handle_open_webui,
                on_export_diagnostics=self._handle_export_diagnostics,
                on_check_update=self._handle_check_update,
                on_import_update=self._handle_import_update,
                on_restore_update_backup=self._handle_restore_update_backup,
                on_factory_reset=self._handle_factory_reset,
                on_reconfigure=self.show_setup_wizard,
            )
            self.main_window.bind_feishu_handlers(
                on_save=self._handle_save_feishu_channel,
                on_test=self._handle_test_feishu_channel,
                on_enable=self._handle_enable_feishu_channel,
                on_disable=self._handle_disable_feishu_channel,
                on_open_help=self._handle_open_feishu_help,
            )
            self.main_window.bind_social_channel_handlers(
                on_install_wechat=self._handle_install_wechat_channel,
                on_login_wechat=self._handle_login_wechat_channel,
                on_confirm_wechat=self._handle_confirm_wechat_channel,
                on_open_wechat_help=self._handle_open_wechat_help,
                on_enable_wechat=self._handle_enable_wechat_channel,
                on_disable_wechat=self._handle_disable_wechat_channel,
                on_open_qq_help=self._handle_open_qq_help,
                on_save_qq=self._handle_save_qq_channel,
                on_test_qq=self._handle_test_qq_channel,
                on_enable_qq=self._handle_enable_qq_channel,
                on_disable_qq=self._handle_disable_qq_channel,
                on_install_wecom=self._handle_install_wecom_channel,
                on_save_wecom=self._handle_save_wecom_channel,
                on_test_wecom=self._handle_test_wecom_channel,
                on_enable_wecom=self._handle_enable_wecom_channel,
                on_disable_wecom=self._handle_disable_wecom_channel,
            )
        self.main_window.apply_view_state(view_state)
        self.main_window.apply_feishu_channel_state(self.controller.load_feishu_channel_state())
        self.main_window.apply_wechat_channel_state(self.controller.load_wechat_channel_state())
        self.main_window.apply_qq_channel_state(self.controller.load_qq_channel_state())
        self.main_window.apply_wecom_channel_state(self.controller.load_wecom_channel_state())
        self._refresh_runtime_console()
        self._runtime_poll_timer.start()
        self.main_window.show()
        if self.wizard_window:
            self.wizard_window.hide()

    def show_setup_wizard(self) -> None:
        provider_templates = self.registry.load()
        self.wizard_window = SetupWizardWindow(provider_templates)
        self.wizard_window.bind_handlers(on_complete=self._complete_setup, on_cancel=self.show_main_window)
        self.wizard_window.show()
        if self.main_window:
            self.main_window.hide()
        self._runtime_poll_timer.stop()

    def _complete_setup(self, config, sensitive) -> None:
        self.controller.configure(config, sensitive)
        self.show_main_window()

    def _handle_start(self) -> None:
        if self._is_action_busy("start_runtime"):
            return
        self._show_pending_runtime_state("start")
        self._run_background_action("start_runtime", self.controller.start_runtime, lambda _: self._refresh_main_view(), call_on_none=True)

    def _handle_stop(self) -> None:
        self._run_background_action("stop_runtime", self.controller.stop_runtime, lambda _: self._refresh_main_view(), call_on_none=True)

    def _handle_restart(self) -> None:
        if self._is_action_busy("restart_runtime"):
            return
        self._show_pending_runtime_state("restart")
        self._run_background_action("restart_runtime", self.controller.restart_runtime, lambda _: self._refresh_main_view(), call_on_none=True)

    def _handle_export_diagnostics(self) -> None:
        bundle_path = self._run_with_error_boundary(self.controller.export_diagnostics_bundle)
        if bundle_path:
            self._show_info(f"诊断包已导出到：{bundle_path}")

    def _handle_import_update(self) -> None:
        selected_dir = self._select_update_package_dir()
        if not selected_dir:
            return
        self._run_background_action(
            "import_update",
            lambda: self.controller.import_update_package(Path(selected_dir)),
            lambda imported_version: self._show_info(f"已导入更新包：{imported_version}。请重新启动启动器完成切换。"),
        )

    def _handle_check_update(self) -> None:
        self._run_background_action("check_update", self.controller.check_for_updates, self._handle_update_metadata)

    def _handle_update_metadata(self, metadata: UpdateCheckResult) -> None:
        if metadata is None:
            return
        if not metadata.update_available:
            self._show_info(f"当前已经是最新版本：{metadata.latest_version}")
            return
        if not self._confirm_online_update(metadata):
            return
        self._run_background_action(
            "check_update",
            lambda: self.controller.download_and_import_update(metadata),
            lambda imported_version: self._show_info(f"已更新到 {imported_version}。请重新启动启动器完成切换。"),
        )

    def _handle_restore_update_backup(self) -> None:
        if not self._confirm_restore_update_backup():
            return
        selected_dir = self._select_update_backup_dir()
        if not selected_dir:
            return
        backup_dir = Path(selected_dir)
        self._run_background_action(
            "restore_update_backup",
            lambda: self.controller.restore_update_backup(backup_dir),
            lambda restored_version: self._show_restore_update_backup_result(restored_version, backup_dir),
        )

    def _show_restore_update_backup_result(self, restored_version: str | None, backup_dir: Path) -> None:
        if restored_version is not None:
            version_label = restored_version or backup_dir.name
            self._show_info(f"已恢复更新备份：{version_label}。请重新启动启动器完成切换。")

    def _handle_factory_reset(self) -> None:
        if not self._confirm_factory_reset():
            return
        reset_ok = self._run_with_error_boundary(self.controller.reset_factory_state)
        if reset_ok:
            self._show_info("已恢复到首次配置状态，正在返回首次向导。")
            self.show_setup_wizard()

    def _handle_open_webui(self) -> None:
        view_state = self.controller.load_view_state()
        if not view_state.webui_url:
            self._show_error("当前还没有可打开的 WebUI 地址。")
            return
        webbrowser.open_new_tab(view_state.webui_url)

    def _handle_save_feishu_channel(self) -> None:
        if not self.main_window:
            return
        state = self.controller.save_feishu_channel(
            self.main_window.feishu_app_id_input.text(),
            self.main_window.feishu_app_secret_input.text(),
            self.main_window.feishu_bot_name_input.text(),
        )
        self._apply_feishu_channel_state(state)

    def _handle_test_feishu_channel(self) -> None:
        self._handle_save_feishu_channel()
        self._run_background_action(
            "test_feishu_channel",
            self.controller.test_feishu_channel,
            self._apply_feishu_channel_state,
        )

    def _handle_enable_feishu_channel(self) -> None:
        self._run_background_action(
            "enable_feishu_channel",
            self.controller.enable_feishu_channel,
            self._apply_feishu_channel_state,
        )

    def _handle_disable_feishu_channel(self) -> None:
        state = self._run_with_error_boundary(self.controller.disable_feishu_channel)
        if state is not None:
            self._apply_feishu_channel_state(state)

    def _handle_open_feishu_help(self) -> None:
        help_path = self.paths.assets_dir / "guide" / "setup-feishu.html"
        if not help_path.exists():
            self._show_error("飞书接入帮助页尚未打包。")
            return
        webbrowser.open_new_tab(help_path.as_uri())

    def _handle_install_wechat_channel(self) -> None:
        self._run_background_action("install_wechat_channel", self.controller.install_wechat_channel, self._apply_wechat_channel_state)

    def _handle_login_wechat_channel(self) -> None:
        self._run_background_action(
            "login_wechat_channel",
            self.controller.login_wechat_channel,
            lambda state: (self._apply_wechat_channel_state(state), self._refresh_main_view()),
        )

    def _handle_confirm_wechat_channel(self) -> None:
        self._run_background_action(
            "confirm_wechat_channel",
            self.controller.confirm_wechat_channel_login,
            lambda state: (self._apply_wechat_channel_state(state), self._refresh_main_view()),
        )

    def _handle_enable_wechat_channel(self) -> None:
        self._run_background_action("enable_wechat_channel", self.controller.enable_wechat_channel, self._apply_wechat_channel_state)

    def _handle_disable_wechat_channel(self) -> None:
        state = self._run_with_error_boundary(self.controller.disable_wechat_channel)
        if state is not None:
            self._apply_wechat_channel_state(state)

    def _handle_open_wechat_help(self) -> None:
        help_path = self.paths.assets_dir / "guide" / "setup-wechat.html"
        if not help_path.exists():
            self._show_error("微信接入帮助页尚未打包。")
            return
        webbrowser.open_new_tab(help_path.as_uri())

    def _handle_save_qq_channel(self) -> None:
        if not self.main_window:
            return
        state = self.controller.save_qq_channel(
            self.main_window.qq_app_id_input.text(),
            self.main_window.qq_app_secret_input.text(),
        )
        self._apply_qq_channel_state(state)

    def _handle_test_qq_channel(self) -> None:
        self._handle_save_qq_channel()
        self._run_background_action("test_qq_channel", self.controller.test_qq_channel, self._apply_qq_channel_state)

    def _handle_enable_qq_channel(self) -> None:
        self._run_background_action("enable_qq_channel", self.controller.enable_qq_channel, self._apply_qq_channel_state)

    def _handle_disable_qq_channel(self) -> None:
        state = self._run_with_error_boundary(self.controller.disable_qq_channel)
        if state is not None:
            self._apply_qq_channel_state(state)

    def _handle_open_qq_help(self) -> None:
        help_path = self.paths.assets_dir / "guide" / "setup-qq.html"
        if not help_path.exists():
            self._show_error("QQ 接入帮助页尚未打包。")
            return
        webbrowser.open_new_tab(help_path.as_uri())

    def _handle_install_wecom_channel(self) -> None:
        self._run_background_action("install_wecom_channel", self.controller.install_wecom_channel, self._apply_wecom_channel_state)

    def _handle_save_wecom_channel(self) -> None:
        if not self.main_window:
            return
        state = self.controller.save_wecom_channel(
            self.main_window.wecom_bot_id_input.text(),
            self.main_window.wecom_secret_input.text(),
        )
        self._apply_wecom_channel_state(state)

    def _handle_test_wecom_channel(self) -> None:
        self._handle_save_wecom_channel()
        self._run_background_action("test_wecom_channel", self.controller.test_wecom_channel, self._apply_wecom_channel_state)

    def _handle_enable_wecom_channel(self) -> None:
        self._run_background_action("enable_wecom_channel", self.controller.enable_wecom_channel, self._apply_wecom_channel_state)

    def _handle_disable_wecom_channel(self) -> None:
        state = self._run_with_error_boundary(self.controller.disable_wecom_channel)
        if state is not None:
            self._apply_wecom_channel_state(state)

    def _apply_feishu_channel_state(self, state) -> None:
        if self.main_window and hasattr(self.main_window, "apply_feishu_channel_state"):
            self.main_window.apply_feishu_channel_state(state)

    def _apply_wechat_channel_state(self, state) -> None:
        if self.main_window and hasattr(self.main_window, "apply_wechat_channel_state"):
            self.main_window.apply_wechat_channel_state(state)

    def _apply_qq_channel_state(self, state) -> None:
        if self.main_window and hasattr(self.main_window, "apply_qq_channel_state"):
            self.main_window.apply_qq_channel_state(state)

    def _apply_wecom_channel_state(self, state) -> None:
        if self.main_window and hasattr(self.main_window, "apply_wecom_channel_state"):
            self.main_window.apply_wecom_channel_state(state)

    def _refresh_main_view(self) -> None:
        if self.main_window:
            self.main_window.apply_view_state(self.controller.load_view_state())
            if hasattr(self.controller, "load_feishu_channel_state"):
                self._apply_feishu_channel_state(self.controller.load_feishu_channel_state())
            if hasattr(self.controller, "load_wechat_channel_state"):
                self._apply_wechat_channel_state(self.controller.load_wechat_channel_state())
            if hasattr(self.controller, "load_qq_channel_state"):
                self._apply_qq_channel_state(self.controller.load_qq_channel_state())
            if hasattr(self.controller, "load_wecom_channel_state"):
                self._apply_wecom_channel_state(self.controller.load_wecom_channel_state())
            self._refresh_runtime_console()

    def _poll_runtime_state(self) -> None:
        if not self.main_window:
            return
        self.main_window.apply_view_state(self.controller.load_view_state())
        self._refresh_runtime_console()

    def _refresh_runtime_console(self) -> None:
        if not self.main_window or not hasattr(self.main_window, "apply_runtime_console"):
            return
        output = self._runtime_console_output()
        summary = self._runtime_console_summary(output)
        self.main_window.apply_runtime_console(summary, output)

    def _runtime_console_output(self) -> str:
        if not hasattr(self, "paths"):
            return (
                "启动后这里会实时显示 OpenClaw 输出。\n"
                "看到 [gateway] ready 说明主服务起来了。\n"
                "看到 ws client ready 说明飞书私聊链路已经连上。"
            )
        stdout_path = self.paths.logs_dir / "openclaw-runtime.out.log"
        stderr_path = self.paths.logs_dir / "openclaw-runtime.err.log"
        sections: list[str] = []
        stdout_text = self._tail_text(stdout_path)
        stderr_text = self._tail_text(stderr_path)
        if stdout_text:
            sections.append("[stdout]\n" + stdout_text)
        if stderr_text:
            sections.append("[stderr]\n" + stderr_text)
        if sections:
            return "\n\n".join(sections)
        return (
            "启动后这里会实时显示 OpenClaw 输出。\n"
            "看到 [gateway] ready 说明主服务起来了。\n"
            "看到 ws client ready 说明飞书私聊链路已经连上。"
        )

    def _tail_text(self, path: Path, *, max_chars: int = 12000) -> str:
        if not path.exists():
            return ""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        if len(text) <= max_chars:
            return text.strip()
        return text[-max_chars:].strip()

    def _runtime_console_summary(self, output: str) -> str:
        if "ws client ready" in output:
            return "Gateway 已就绪，飞书已连接"
        if "WebSocket client started" in output:
            return "Gateway 已就绪，飞书正在建立连接"
        if "[gateway] ready" in output:
            return "Gateway 已就绪"
        if "[gateway] starting" in output or "starting HTTP server" in output:
            return "正在启动 OpenClaw…"
        if "RuntimeError" in output or "Error:" in output or "ERR_" in output:
            return "启动失败，请查看下方错误日志"
        return "等待启动日志…"

    def _show_pending_runtime_state(self, action: str) -> None:
        if self.main_window:
            self.main_window.apply_view_state(self.controller.load_pending_runtime_view_state(action))
            self.app.processEvents()

    def _run_with_error_boundary(self, action):
        try:
            return action()
        except Exception as exc:  # noqa: BLE001
            self._show_error(format_runtime_error(exc))
            return None

    def _run_background_action(self, action_key: str, action, on_success, *, call_on_none: bool = False) -> bool:
        if not hasattr(self, "_busy_actions"):
            self._busy_actions = set()
        if action_key in self._busy_actions:
            return False
        has_background_runner = hasattr(self, "_background_executor") and hasattr(self, "_background_signals")
        self._busy_actions.add(action_key)
        if has_background_runner:
            self._set_action_busy(action_key, True)
        if not has_background_runner:
            result = self._run_with_error_boundary(action)
            self._busy_actions.discard(action_key)
            if result is not None or call_on_none:
                on_success(result)
            return True
        future = self._background_executor.submit(action)
        future.add_done_callback(lambda completed: self._background_signals.completed.emit(action_key, completed, on_success, call_on_none))
        return True

    def _finish_background_action(self, action_key: str, future: Future, on_success, call_on_none: bool) -> None:
        self._busy_actions.discard(action_key)
        self._set_action_busy(action_key, False)
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001
            self._show_error(format_runtime_error(exc))
            return
        if result is not None or call_on_none:
            on_success(result)

    def _is_action_busy(self, action_key: str) -> bool:
        return action_key in getattr(self, "_busy_actions", set())

    def _set_action_busy(self, action_key: str, busy: bool) -> None:
        if self.main_window and hasattr(self.main_window, "set_action_busy"):
            self.main_window.set_action_busy(action_key, busy)

    def _shutdown_background_executor(self) -> None:
        self._background_executor.shutdown(wait=False, cancel_futures=True)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self.main_window or self.wizard_window, "OpenClaw Portable", message)

    def _show_info(self, message: str) -> None:
        QMessageBox.information(self.main_window or self.wizard_window, "OpenClaw Portable", message)

    def _select_update_package_dir(self) -> str:
        return QFileDialog.getExistingDirectory(
            self.main_window or self.wizard_window,
            "选择更新包目录",
            str(self.paths.project_root.parent),
        )

    def _select_update_backup_dir(self) -> str:
        return QFileDialog.getExistingDirectory(
            self.main_window or self.wizard_window,
            "选择要恢复的更新备份目录",
            str(self.paths.state_dir / "backups" / "updates"),
        )

    def _confirm_factory_reset(self) -> bool:
        result = QMessageBox.question(
            self.main_window or self.wizard_window,
            "OpenClaw Portable",
            "这会清空当前启动器配置、临时日志和缓存，并返回首次向导。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def _confirm_restore_update_backup(self) -> bool:
        result = QMessageBox.question(
            self.main_window or self.wizard_window,
            "OpenClaw Portable",
            "这会用历史更新备份恢复当前程序分发内容，不会覆盖 state/，并会先自动备份当前版本。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def _confirm_online_update(self, metadata: UpdateCheckResult) -> bool:
        notes_text = "\n".join(f"- {note}" for note in metadata.notes) if metadata.notes else "- 暂无更新说明"
        result = QMessageBox.question(
            self.main_window or self.wizard_window,
            "OpenClaw Portable",
            f"发现新版本：{metadata.latest_version}\n\n更新说明：\n{notes_text}\n\n是否现在下载并导入更新？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes
