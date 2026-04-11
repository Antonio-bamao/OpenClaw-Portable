from __future__ import annotations

import shutil

from launcher.core.paths import PortablePaths


class FactoryResetService:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def reset(self) -> None:
        self.paths.ensure_directories()
        self._remove_file(self.paths.config_file)
        self._remove_file(self.paths.env_file)
        self._clear_directory(self.paths.provider_templates_dir)
        self._clear_directory(self.paths.logs_dir)
        self._clear_directory(self.paths.cache_dir)
        self._clear_directory(self.paths.state_dir / "sessions")
        self._clear_directory(self.paths.state_dir / "channels")
        self.paths.ensure_directories()

    def _remove_file(self, target) -> None:
        if target.exists():
            target.unlink()

    def _clear_directory(self, target) -> None:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
