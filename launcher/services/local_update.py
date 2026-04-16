from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.update_manifest import DEFAULT_UPDATE_ENTRY_NAMES, validate_update_manifest
from launcher.services.update_signature import (
    DEFAULT_UPDATE_SIGNING_KEY_ID,
    DEFAULT_UPDATE_SIGNING_PUBLIC_KEY,
    verify_update_signature,
)


UPDATE_ENTRY_NAMES = DEFAULT_UPDATE_ENTRY_NAMES
PACKAGE_PAYLOAD_ENTRY_NAMES = tuple(entry_name for entry_name in UPDATE_ENTRY_NAMES if entry_name != "version.json")
VERSION_PATTERN = re.compile(r"^v?(?P<core>\d+(?:\.\d+)*)(?:-(?P<suffix>[A-Za-z0-9.-]+))?$")


@dataclass(frozen=True)
class LocalUpdateImportResult:
    imported_version: str
    backup_dir: Path
    updated_entries: list[str]


@dataclass(frozen=True)
class RestoreUpdateBackupResult:
    restored_version: str
    backup_dir: Path
    restored_entries: list[str]
    source_backup_dir: Path


class LocalUpdateImportService:
    def __init__(
        self,
        paths: PortablePaths,
        *,
        signature_key_id: str = DEFAULT_UPDATE_SIGNING_KEY_ID,
        signature_public_key_b64: str = DEFAULT_UPDATE_SIGNING_PUBLIC_KEY,
        signature_public_keys: Mapping[str, str] | None = None,
    ) -> None:
        self.paths = paths
        self.signature_key_id = signature_key_id
        self.signature_public_key_b64 = signature_public_key_b64
        self.signature_public_keys = (
            dict(signature_public_keys) if signature_public_keys is not None else {signature_key_id: signature_public_key_b64}
        )

    def import_package(self, source_root: Path) -> LocalUpdateImportResult:
        self.paths.ensure_directories()
        source_root = source_root.resolve()
        target_root = self.paths.project_root.resolve()
        if source_root == target_root:
            raise ValueError("更新包目录不能与当前便携包目录相同。")
        _, incoming_version, _ = self._validate_import_source(source_root)

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
                updated_entries.append(entry_name)
                self._remove_entry(target_entry)
                self._copy_entry(source_entry, target_entry)
        except Exception:
            self._rollback(updated_entries, backup_dir)
            raise

        return LocalUpdateImportResult(
            imported_version=incoming_version,
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
        return self._read_version_from_file(version_file, label="version.json")

    def _read_version_from_file(self, version_file: Path, *, label: str) -> str:
        try:
            version_info = json.loads(version_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} 不是合法 JSON。") from exc
        version = str(version_info.get("version") or "").strip()
        if not version:
            raise ValueError(f"{label} 缺少有效的版本号。")
        self._version_key(version, label=label)
        return version

    def _validate_import_source(self, source_root: Path) -> tuple[Path, str, list[str]]:
        version_file = source_root / "version.json"
        if not version_file.exists():
            raise FileNotFoundError("更新包缺少 version.json。")

        available_entries = [entry_name for entry_name in PACKAGE_PAYLOAD_ENTRY_NAMES if (source_root / entry_name).exists()]
        if not available_entries:
            raise FileNotFoundError("更新包中没有可导入的程序文件。请重新选择完整的便携包目录。")

        incoming_version = self._read_version_from_file(version_file, label="更新包的 version.json")
        current_version_file = self.paths.project_root / "version.json"
        if not current_version_file.exists():
            raise FileNotFoundError("当前便携包缺少 version.json，无法判断更新顺序。")
        current_version = self._read_version_from_file(current_version_file, label="当前便携包的 version.json")

        version_comparison = self._compare_versions(incoming_version, current_version)
        if version_comparison == 0:
            raise ValueError(f"当前已经是版本 {incoming_version}，无需重复导入。")
        if version_comparison < 0:
            raise ValueError(
                f"所选更新包版本 {incoming_version} 低于当前版本 {current_version}。"
                "如果要回退，请改用“恢复更新备份”。"
            )
        verify_update_signature(
            source_root,
            expected_key_id=self.signature_key_id,
            public_key_b64=self.signature_public_key_b64,
            trusted_public_keys=self.signature_public_keys,
        )
        validate_update_manifest(source_root, expected_version=incoming_version, required_entries=available_entries + ["version.json"])
        return version_file, incoming_version, available_entries

    def _compare_versions(self, left: str, right: str) -> int:
        left_core, left_stability, left_suffix = self._version_key(left, label="版本号")
        right_core, right_stability, right_suffix = self._version_key(right, label="版本号")
        max_length = max(len(left_core), len(right_core))
        for index in range(max_length):
            left_part = left_core[index] if index < len(left_core) else 0
            right_part = right_core[index] if index < len(right_core) else 0
            if left_part != right_part:
                return 1 if left_part > right_part else -1
        if left_stability != right_stability:
            return 1 if left_stability > right_stability else -1
        if left_suffix == right_suffix:
            return 0
        return 1 if left_suffix > right_suffix else -1

    def _version_key(self, version: str, *, label: str) -> tuple[tuple[int, ...], int, str]:
        match = VERSION_PATTERN.fullmatch(version.strip())
        if not match:
            raise ValueError(f"{label} 缺少有效的版本号。")
        core = tuple(int(part) for part in match.group("core").split("."))
        suffix = (match.group("suffix") or "").strip()
        stability_rank = 1 if not suffix else 0
        return core, stability_rank, suffix

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
            if os.name == "nt":
                self._copy_directory_with_robocopy(source, destination)
                return
            shutil.copytree(source, destination, dirs_exist_ok=True)
            return
        shutil.copy2(source, destination)

    def _copy_directory_with_robocopy(self, source: Path, destination: Path) -> None:
        command = [
            "robocopy",
            str(source),
            str(destination),
            "/E",
            "/R:1",
            "/W:1",
            "/MT:8",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/NP",
        ]
        result = subprocess.run(command, check=False)
        if result.returncode >= 8:
            raise RuntimeError(f"robocopy failed while copying {source} to {destination} with exit code {result.returncode}")

    def _remove_entry(self, target: Path) -> None:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()


class RestoreUpdateBackupService(LocalUpdateImportService):
    def restore_backup(self, backup_root: Path) -> RestoreUpdateBackupResult:
        self.paths.ensure_directories()
        backup_root = backup_root.resolve()
        target_root = self.paths.project_root.resolve()
        if backup_root == target_root:
            raise ValueError("恢复备份目录不能与当前便携包目录相同。")
        if not backup_root.exists():
            raise FileNotFoundError("指定的更新备份目录不存在。")

        restorable_entries = [entry_name for entry_name in UPDATE_ENTRY_NAMES if (backup_root / entry_name).exists()]
        if not restorable_entries:
            raise FileNotFoundError("备份目录中没有可恢复的分发内容。")

        rollback_backup_dir = self._create_backup_dir()
        restored_entries: list[str] = []

        try:
            for entry_name in restorable_entries:
                source_entry = backup_root / entry_name
                target_entry = target_root / entry_name
                rollback_entry = rollback_backup_dir / entry_name
                if target_entry.exists():
                    rollback_entry.parent.mkdir(parents=True, exist_ok=True)
                    self._copy_entry(target_entry, rollback_entry)
                restored_entries.append(entry_name)
                self._remove_entry(target_entry)
                self._copy_entry(source_entry, target_entry)
        except Exception:
            self._rollback(restored_entries, rollback_backup_dir)
            raise

        version_file = backup_root / "version.json"
        restored_version = self._read_version(version_file) if version_file.exists() else ""
        return RestoreUpdateBackupResult(
            restored_version=restored_version,
            backup_dir=rollback_backup_dir,
            restored_entries=restorable_entries,
            source_backup_dir=backup_root,
        )
