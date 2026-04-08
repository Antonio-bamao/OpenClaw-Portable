from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

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
        self._run_with_error_boundary(self.controller.start_runtime)
        self._refresh_main_view()

    def _handle_stop(self) -> None:
        self._run_with_error_boundary(self.controller.stop_runtime)
        self._refresh_main_view()

    def _handle_restart(self) -> None:
        self._run_with_error_boundary(self.controller.restart_runtime)
        self._refresh_main_view()

    def _handle_open_webui(self) -> None:
        view_state = self.controller.load_view_state()
        if not view_state.webui_url:
            self._show_error("当前还没有可打开的 WebUI 地址。")
            return
        webbrowser.open_new_tab(view_state.webui_url)

    def _refresh_main_view(self) -> None:
        if self.main_window:
            self.main_window.apply_view_state(self.controller.load_view_state())

    def _run_with_error_boundary(self, action) -> None:
        try:
            action()
        except Exception as exc:  # noqa: BLE001
            self._show_error(format_runtime_error(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self.main_window or self.wizard_window, "OpenClaw Portable", message)
