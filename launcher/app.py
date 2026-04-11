from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from launcher.bootstrap import AppRoute, LauncherBootstrap
from launcher.core.paths import PortablePaths
from launcher.services.controller import LauncherController
from launcher.services.provider_registry import ProviderTemplateRegistry
from launcher.services.runtime_errors import format_runtime_error
from launcher.services.runtime_mode import resolve_runtime_mode
from launcher.ui.main_window import OpenClawLauncherWindow
from launcher.ui.theme import preferred_font
from launcher.ui.wizard import SetupWizardWindow


class OpenClawLauncherApplication:
    def __init__(self, project_root: Path | None = None, node_command: str = "node", runtime_mode: str | None = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.paths = PortablePaths.for_root(self.project_root)
        selected_runtime_mode = resolve_runtime_mode(self.paths, requested_mode=runtime_mode)
        self.controller = LauncherController(self.paths, node_command=node_command, runtime_mode=selected_runtime_mode)
        self.registry = ProviderTemplateRegistry(self.paths.provider_templates_dir)
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setFont(preferred_font())
        self.main_window: OpenClawLauncherWindow | None = None
        self.wizard_window: SetupWizardWindow | None = None

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
                on_import_update=self._handle_import_update,
                on_restore_update_backup=self._handle_restore_update_backup,
                on_factory_reset=self._handle_factory_reset,
                on_reconfigure=self.show_setup_wizard,
            )
        self.main_window.apply_view_state(view_state)
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

    def _complete_setup(self, config, sensitive) -> None:
        self.controller.configure(config, sensitive)
        self.show_main_window()

    def _handle_start(self) -> None:
        self._show_pending_runtime_state("start")
        self._run_with_error_boundary(self.controller.start_runtime)
        self._refresh_main_view()

    def _handle_stop(self) -> None:
        self._run_with_error_boundary(self.controller.stop_runtime)
        self._refresh_main_view()

    def _handle_restart(self) -> None:
        self._show_pending_runtime_state("restart")
        self._run_with_error_boundary(self.controller.restart_runtime)
        self._refresh_main_view()

    def _handle_export_diagnostics(self) -> None:
        bundle_path = self._run_with_error_boundary(self.controller.export_diagnostics_bundle)
        if bundle_path:
            self._show_info(f"诊断包已导出到：{bundle_path}")

    def _handle_import_update(self) -> None:
        selected_dir = self._select_update_package_dir()
        if not selected_dir:
            return
        imported_version = self._run_with_error_boundary(lambda: self.controller.import_update_package(Path(selected_dir)))
        if imported_version:
            self._show_info(f"已导入更新包：{imported_version}。请重新启动启动器完成切换。")

    def _handle_restore_update_backup(self) -> None:
        if not self._confirm_restore_update_backup():
            return
        selected_dir = self._select_update_backup_dir()
        if not selected_dir:
            return
        backup_dir = Path(selected_dir)
        restored_version = self._run_with_error_boundary(lambda: self.controller.restore_update_backup(backup_dir))
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

    def _refresh_main_view(self) -> None:
        if self.main_window:
            self.main_window.apply_view_state(self.controller.load_view_state())

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
