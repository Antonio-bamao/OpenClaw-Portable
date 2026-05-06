from __future__ import annotations

import sys
import webbrowser
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QMessageBox, QSystemTrayIcon

from launcher.bootstrap import AppRoute, LauncherBootstrap
from launcher.core.paths import PortablePaths
from launcher.services.controller import LauncherController
from launcher.services.provider_registry import ProviderTemplateRegistry
from launcher.services.runtime_errors import format_runtime_error
from launcher.services.runtime_mode import resolve_runtime_mode
from launcher.services.online_update import UpdateCheckResult
from launcher.services.process_lock import SingleInstanceLock
from launcher.services.window_preferences import CloseAction, WindowPreferenceStore
from launcher.ui.close_dialog import CloseActionDialog
from launcher.ui.main_window import OpenClawLauncherWindow
from launcher.ui.theme import ACCENT, ACCENT_DEEP, BORDER, FIELD, METAL, PANEL, PRIMARY, SURFACE, TEXT, preferred_font
from launcher.ui.unlock_dialog import UnlockDialog
from launcher.ui.window_branding import apply_app_icon, apply_windows_title_bar_palette, load_app_icon
from launcher.ui.wizard import SetupWizardWindow


def message_box_stylesheet() -> str:
    return f"""
QMessageBox {{
    background-color: {PANEL};
    color: {TEXT};
    border-top: 4px solid {ACCENT};
}}
QMessageBox QLabel {{
    color: {TEXT};
    background-color: transparent;
    font-size: 14px;
}}
QMessageBox QPushButton {{
    background-color: {FIELD};
    color: {PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 8px 18px;
    min-width: 86px;
    min-height: 34px;
    font-weight: 700;
}}
QMessageBox QPushButton:hover {{
    background-color: {SURFACE};
    border-color: {PRIMARY};
}}
QMessageBox QPushButton:pressed {{
    background-color: {METAL};
}}
QMessageBox QPushButton:default {{
    background-color: {ACCENT};
    color: #ffffff;
    border: 1px solid {ACCENT_DEEP};
}}
""".strip()


CODEBUDDY_GUIDE_URLS = {
    "feishu": "https://www.codebuddy.cn/docs/workbuddy/Feishu-Guide",
    "wechat": "https://www.codebuddy.cn/docs/workbuddy/WeixinBot-Guide",
    "qq": "https://www.codebuddy.cn/docs/workbuddy/QQ-Guide",
    "wecom": "https://www.codebuddy.cn/docs/workbuddy/Wecom-Guide",
}


class BackgroundTaskSignals(QObject):
    completed = Signal(str, object, object, bool)


class OpenClawLauncherApplication:
    def __init__(self, project_root: Path | None = None, node_command: str = "node", runtime_mode: str | None = None) -> None:
        self.project_root = project_root or self._default_project_root()
        self.paths = PortablePaths.for_root(self.project_root)
        self.instance_lock = SingleInstanceLock(self.paths.temp_root / "OpenClawLauncher.lock")
        self._instance_lock_acquired = False
        selected_runtime_mode = resolve_runtime_mode(self.paths, requested_mode=runtime_mode)
        self.controller = LauncherController(self.paths, node_command=node_command, runtime_mode=selected_runtime_mode)
        self.registry = ProviderTemplateRegistry(self.paths.provider_templates_dir)
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setFont(preferred_font())
        self.app.setQuitOnLastWindowClosed(False)
        apply_app_icon(self.app, None, self.paths.assets_dir)
        self.close_preferences = WindowPreferenceStore(self.paths.state_dir)
        self.main_window: OpenClawLauncherWindow | None = None
        self.wizard_window: SetupWizardWindow | None = None
        self.tray_icon: QSystemTrayIcon | None = None
        self.tray_menu: QMenu | None = None
        self._tray_message_shown = False
        self._exiting = False
        self._busy_actions: set[str] = set()
        self._auto_start_attempted = False
        self._auto_opened_webui = False
        self._background_executor = ThreadPoolExecutor(max_workers=1)
        self._background_signals = BackgroundTaskSignals()
        self._background_signals.completed.connect(self._finish_background_action)
        self._runtime_poll_timer = QTimer()
        self._runtime_poll_timer.setInterval(1000)
        self._runtime_poll_timer.timeout.connect(self._poll_runtime_state)
        self._setup_tray_icon()
        self.app.aboutToQuit.connect(self._handle_about_to_quit)

    @staticmethod
    def _default_project_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent

    def run(self) -> int:
        if not self.instance_lock.acquire():
            return 0
        self._instance_lock_acquired = True
        route = LauncherBootstrap(self.paths).initial_route()
        if route == AppRoute.SETUP_WIZARD:
            self.show_setup_wizard()
        else:
            if not self._ensure_security_unlocked():
                return 0
            self.show_main_window()
        try:
            return self.app.exec()
        finally:
            self.instance_lock.release()
            self._instance_lock_acquired = False

    def show_main_window(self, *, auto_start: bool = True) -> None:
        if not self._ensure_security_unlocked():
            return
        view_state = self.controller.load_view_state()
        if not self.main_window:
            self.main_window = OpenClawLauncherWindow(view_state)
            self.main_window.set_close_requested_handler(self._handle_main_window_close_request)
            self.main_window.bind_handlers(
                on_start=self._handle_start,
                on_stop=self._handle_stop,
                on_restart=self._handle_restart,
                on_open_webui=self._handle_open_webui,
                on_export_diagnostics=self._handle_export_diagnostics,
                on_check_update=self._handle_check_update,
                on_import_update=self._handle_import_update,
                on_restore_update_backup=self._handle_restore_update_backup,
                on_open_faq=self._handle_open_faq,
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
                on_open_wecom_help=self._handle_open_wecom_help,
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
        apply_app_icon(self.app, self.main_window, self.paths.assets_dir)
        self.main_window.show()
        apply_windows_title_bar_palette(
            self.main_window,
            caption_color="#E8E5DC",
            text_color="#1F2020",
            border_color="#C9C5BA",
        )
        if self.wizard_window:
            self.wizard_window.hide()
        if auto_start:
            self._schedule_auto_start_runtime()

    def _ensure_security_unlocked(self) -> bool:
        if not hasattr(self.controller, "security_requires_password_unlock"):
            return True
        if getattr(self.controller, "security_needs_initial_setup", lambda: False)():
            created = self._prompt_security_setup()
            if created is None:
                return False
            password, _trust_device = created
            if not password.strip():
                self._show_error("管理密码不能为空。")
                return False
            if not self.controller.initialize_security_password(password):
                self._show_error("本地保险箱初始化失败，请重试。")
                return False
            self._show_info("已启用本地保险箱，API Key 将迁移到加密存储。")
            return True
        if hasattr(self.controller, "unlock_security_with_trusted_device") and self.controller.unlock_security_with_trusted_device():
            return True
        if not self.controller.security_requires_password_unlock():
            return True
        unlock = self._prompt_security_unlock()
        if unlock is None:
            return False
        password, trust_device = unlock
        if not self.controller.unlock_security_with_password(password, trust_device=trust_device):
            self._show_error("管理密码不正确，无法解锁本地保险箱。")
            return False
        if getattr(self.controller, "security_last_unlock_was_new_device", lambda: False)():
            self.controller.mark_channels_for_new_device()
            self._show_info("已解锁本地保险箱。检测到新的电脑环境，各渠道已进入重新连接/确认状态。")
        return True

    def _prompt_security_unlock(self) -> tuple[str, bool] | None:
        dialog = UnlockDialog(self.main_window or self.wizard_window)
        apply_app_icon(self.app, dialog, self.paths.assets_dir)
        apply_windows_title_bar_palette(
            dialog,
            caption_color="#E8E5DC",
            text_color="#1F2020",
            border_color="#C9C5BA",
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return None
        return dialog.password, dialog.trust_device

    def _prompt_security_setup(self) -> tuple[str, bool] | None:
        dialog = UnlockDialog(
            self.main_window or self.wizard_window,
            title="启用本地保险箱",
            description="当前便携包已有配置，但还没有真正的管理密码保护。请设置管理密码，用于加密模型 Key 和各渠道凭据；换电脑时也会用它解锁。",
            button_text="启用",
        )
        apply_app_icon(self.app, dialog, self.paths.assets_dir)
        apply_windows_title_bar_palette(
            dialog,
            caption_color="#E8E5DC",
            text_color="#1F2020",
            border_color="#C9C5BA",
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return None
        return dialog.password, True

    def _setup_tray_icon(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = load_app_icon(self.paths.assets_dir)
        if not icon:
            icon = self.app.windowIcon()
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.tray_icon.setToolTip("OpenClaw Portable")
        self.tray_menu = QMenu()
        open_action = QAction("打开控制台", self.tray_menu)
        open_action.triggered.connect(self._restore_from_tray)
        exit_action = QAction("完全退出", self.tray_menu)
        exit_action.triggered.connect(self._exit_application)
        self.tray_menu.addAction(open_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._handle_tray_activated)
        self.tray_icon.show()

    def _handle_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        if not self.main_window:
            self.show_main_window()
            return
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _handle_main_window_close_request(self) -> bool:
        remembered_action = self.close_preferences.load_close_action()
        if remembered_action == CloseAction.MINIMIZE_TO_TRAY:
            self._minimize_main_window_to_tray()
            return False
        if remembered_action == CloseAction.EXIT:
            self._exit_application()
            return True

        close_action, remember_minimize = self._ask_close_action()
        if close_action is None:
            return False
        if close_action == CloseAction.MINIMIZE_TO_TRAY:
            if remember_minimize:
                self.close_preferences.save_close_action(CloseAction.MINIMIZE_TO_TRAY)
            self._minimize_main_window_to_tray()
            return False

        self._exit_application()
        return True

    def _ask_close_action(self) -> tuple[CloseAction | None, bool]:
        dialog = CloseActionDialog(None)
        apply_app_icon(self.app, dialog, self.paths.assets_dir)
        apply_windows_title_bar_palette(
            dialog,
            caption_color="#E8E5DC",
            text_color="#1F2020",
            border_color="#C9C5BA",
        )
        dialog.exec()
        selected_action = dialog.selected_action
        if selected_action is None:
            return None, False
        return selected_action, dialog.remember_choice()

    def _minimize_main_window_to_tray(self) -> None:
        if self.main_window:
            tray_icon = getattr(self, "tray_icon", None)
            if not hasattr(self, "tray_icon") or (tray_icon and tray_icon.isVisible()):
                self.main_window.hide()
                self._show_tray_message()
                return
            self.main_window.showMinimized()

    def _show_tray_message(self) -> None:
        tray_icon = getattr(self, "tray_icon", None)
        if getattr(self, "_tray_message_shown", False) or not tray_icon:
            return
        self._tray_message_shown = True
        tray_icon.showMessage(
            "OpenClaw Portable",
            "OpenClaw 已最小化到系统托盘。右键托盘图标可完全退出。",
            QSystemTrayIcon.MessageIcon.Information,
            3500,
        )

    def _exit_application(self) -> None:
        if getattr(self, "_exiting", False):
            return
        self._exiting = True
        if hasattr(self, "_runtime_poll_timer"):
            self._runtime_poll_timer.stop()
        try:
            self.controller.stop_runtime()
        except Exception as exc:  # noqa: BLE001
            self._show_error(format_runtime_error(exc))
        tray_icon = getattr(self, "tray_icon", None)
        if tray_icon:
            tray_icon.hide()
        self.app.quit()

    def show_setup_wizard(self) -> None:
        provider_templates = self.registry.load()
        self.wizard_window = SetupWizardWindow(provider_templates)
        self.wizard_window.bind_handlers(on_complete=self._complete_setup, on_cancel=self.show_main_window)
        apply_app_icon(self.app, self.wizard_window, self.paths.assets_dir)
        self.wizard_window.show()
        apply_windows_title_bar_palette(
            self.wizard_window,
            caption_color="#E8E5DC",
            text_color="#1F2020",
            border_color="#C9C5BA",
        )
        if self.main_window:
            self.main_window.hide()
        self._runtime_poll_timer.stop()

    def _complete_setup(self, config, sensitive, start_runtime: bool = True) -> None:
        self.controller.configure(config, sensitive)
        self.show_main_window(auto_start=start_runtime)

    def _handle_start(self) -> None:
        if self._is_action_busy("start_runtime"):
            return
        self._show_pending_runtime_state("start")
        self._run_background_action("start_runtime", self.controller.start_runtime, lambda _: self._refresh_main_view(), call_on_none=True)

    def _schedule_auto_start_runtime(self) -> None:
        QTimer.singleShot(0, self._auto_start_runtime)

    def _auto_start_runtime(self) -> None:
        if getattr(self, "_auto_start_attempted", False):
            return
        if not self.controller.should_auto_start_runtime():
            return
        self._auto_start_attempted = True
        self._show_pending_runtime_state("start")
        self._run_background_action(
            "start_runtime",
            self.controller.start_runtime,
            lambda _: self._after_auto_start_runtime(),
            call_on_none=True,
        )

    def _after_auto_start_runtime(self) -> None:
        self._refresh_main_view()

    def _open_webui_once_after_auto_start(self, view_state=None) -> None:
        if getattr(self, "_auto_opened_webui", False):
            return
        view_state = view_state or self.controller.load_view_state()
        if not view_state.webui_url:
            return
        self._auto_opened_webui = True
        webbrowser.open_new_tab(view_state.webui_url)

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

    def _handle_open_faq(self) -> None:
        faq_page = self.paths.assets_dir / "guide" / "faq.html"
        if faq_page.exists():
            webbrowser.open_new_tab(faq_page.resolve().as_uri())
            return
        self._show_error("常见问题页面缺失，请重新解压或更新 OpenClaw Portable。")

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
        self._open_codebuddy_guide("feishu")

    def _handle_install_wechat_channel(self) -> None:
        if self._is_action_busy("install_wechat_channel"):
            return
        if hasattr(self.controller, "wechat_channel_installed") and self.controller.wechat_channel_installed():
            self._apply_wechat_channel_state(self.controller.load_wechat_channel_state())
            self._show_info("微信 ClawBot 插件已安装，无需重复安装。可以直接扫码登录或启用微信。")
            return
        self._show_pending_wechat_channel_state("install")
        self._run_background_action("install_wechat_channel", self.controller.install_wechat_channel, self._apply_wechat_channel_state)

    def _handle_login_wechat_channel(self) -> None:
        if self._is_action_busy("login_wechat_channel"):
            return
        self._show_pending_wechat_channel_state("login")
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
        self._open_codebuddy_guide("wechat")

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
        self._open_codebuddy_guide("qq")

    def _handle_install_wecom_channel(self) -> None:
        if self._is_action_busy("install_wecom_channel"):
            return
        if hasattr(self.controller, "wecom_channel_installed") and self.controller.wecom_channel_installed():
            self._apply_wecom_channel_state(self.controller.load_wecom_channel_state())
            self._show_info("企业微信插件已安装，无需重复安装。请继续填写 Bot ID 和 Secret，或直接启用已有配置。")
            return
        self._run_background_action("install_wecom_channel", self.controller.install_wecom_channel, self._apply_wecom_channel_state)

    def _handle_open_wecom_help(self) -> None:
        self._open_codebuddy_guide("wecom")

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

    def _show_pending_wechat_channel_state(self, action: str) -> None:
        if not self.main_window or not hasattr(self.controller, "load_pending_wechat_channel_state"):
            return
        self._apply_wechat_channel_state(self.controller.load_pending_wechat_channel_state(action))
        if hasattr(self, "app"):
            self.app.processEvents()

    def _open_codebuddy_guide(self, channel: str) -> None:
        webbrowser.open_new_tab(CODEBUDDY_GUIDE_URLS[channel])

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

    def _handle_about_to_quit(self) -> None:
        if hasattr(self, "_runtime_poll_timer"):
            self._runtime_poll_timer.stop()
        if not getattr(self, "_exiting", False):
            try:
                self.controller.stop_runtime()
            except Exception:  # noqa: BLE001
                pass
        self._shutdown_background_executor()

    def _show_error(self, message: str) -> None:
        self._show_message_box(QMessageBox.Icon.Critical, message)

    def _show_info(self, message: str) -> None:
        self._show_message_box(QMessageBox.Icon.Information, message)

    def _show_message_box(
        self,
        icon: QMessageBox.Icon,
        message: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    ) -> QMessageBox.StandardButton:
        dialog = QMessageBox(self.main_window or self.wizard_window)
        dialog.setWindowTitle("OpenClaw Portable")
        dialog.setIcon(icon)
        dialog.setText(message)
        dialog.setStandardButtons(buttons)
        dialog.setDefaultButton(default_button)
        dialog.setStyleSheet(message_box_stylesheet())
        return QMessageBox.StandardButton(dialog.exec())

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
        result = self._show_message_box(
            QMessageBox.Icon.Question,
            "这会清空当前启动器配置、临时日志和缓存，并返回首次向导。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def _confirm_restore_update_backup(self) -> bool:
        result = self._show_message_box(
            QMessageBox.Icon.Question,
            "这会用历史更新备份恢复当前程序分发内容，不会覆盖 state/，并会先自动备份当前版本。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def _confirm_online_update(self, metadata: UpdateCheckResult) -> bool:
        notes_text = "\n".join(f"- {note}" for note in metadata.notes) if metadata.notes else "- 暂无更新说明"
        result = self._show_message_box(
            QMessageBox.Icon.Question,
            f"发现新版本：{metadata.latest_version}\n\n更新说明：\n{notes_text}\n\n是否现在下载并导入更新？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes
