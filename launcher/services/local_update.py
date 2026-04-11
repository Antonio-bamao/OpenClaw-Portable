from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from launcher.core.paths import PortablePaths


UPDATE_ENTRY_NAMES = (
    "OpenClawLauncher.exe",
    "_internal",
    "runtime",
    "assets",
    "tools",
    "README.txt",
    "version.json",
)


@dataclass(frozen=True)
class LocalUpdateImportResult:
    imported_version: str
    backup_dir: Path
    updated_entries: list[str]


class LocalUpdateImportService:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def import_package(self, source_root: Path) -> LocalUpdateImportResult:
        self.paths.ensure_directories()
        source_root = source_root.resolve()
        target_root = self.paths.project_root.resolve()
        if source_root == target_root:
            raise ValueError("更新包目录不能与当前便携包目录相同。")
        version_file = source_root / "version.json"
        if not version_file.exists():
            raise FileNotFoundError("更新包缺少 version.json。")

        backup_dir = self._create_backup_dir()
        updated_entries: list[str] = []

        try:
            for entry_name in UPDATE_ENTRY_NAMES:
                source_entry = source_root / entry_name
                if not source_entry.exists():
                    continue
                target_entry = target_root / entry_name
                backup_entry = backup_dir / entry_name
                if target_entry.exists():
                    backup_entry.parent.mkdir(parents=True, exist_ok=True)
                    self._copy_entry(target_entry, backup_entry)
                self._remove_entry(target_entry)
                self._copy_entry(source_entry, target_entry)
                updated_entries.append(entry_name)
        except Exception:
            self._rollback(updated_entries, backup_dir)
            raise

        return LocalUpdateImportResult(
            imported_version=self._read_version(version_file),
            backup_dir=backup_dir,
            updated_entries=updated_entries,
        )

    def _create_backup_dir(self) -> Path:
        backup_root = self.paths.state_dir / "backups" / "updates"
        backup_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = backup_root / timestamp
        suffix = 1
        while backup_dir.exists():
            suffix += 1
            backup_dir = backup_root / f"{timestamp}-{suffix}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _read_version(self, version_file: Path) -> str:
        version_info = json.loads(version_file.read_text(encoding="utf-8"))
        return str(version_info.get("version") or "").strip()

    def _rollback(self, updated_entries: list[str], backup_dir: Path) -> None:
        for entry_name in updated_entries:
            target_entry = self.paths.project_root / entry_name
            backup_entry = backup_dir / entry_name
            self._remove_entry(target_entry)
            if backup_entry.exists():
                self._copy_entry(backup_entry, target_entry)

    def _copy_entry(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            return
        shutil.copy2(source, destination)

    def _remove_entry(self, target: Path) -> None:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()
