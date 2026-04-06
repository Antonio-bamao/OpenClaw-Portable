from __future__ import annotations

from enum import Enum

from launcher.core.config_store import LauncherConfigStore
from launcher.core.paths import PortablePaths


class AppRoute(str, Enum):
    SETUP_WIZARD = "setup_wizard"
    MAIN_DASHBOARD = "main_dashboard"


class LauncherBootstrap:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths
        self.store = LauncherConfigStore(paths)

    def initial_route(self) -> AppRoute:
        return AppRoute.SETUP_WIZARD if self.store.is_first_run() else AppRoute.MAIN_DASHBOARD
