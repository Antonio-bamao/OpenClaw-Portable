from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


DEFAULT_UPDATE_ENTRY_NAMES = (
    "OpenClawLauncher.exe",
    "_internal",
    "runtime",
    "assets",
    "tools",
    "README.txt",
    "version.json",
)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_directory(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {path}")
    lines: list[str] = []
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        relative_path = file_path.relative_to(path).as_posix()
        lines.append(f"{relative_path}\t{hash_file(file_path)}")
    digest = hashlib.sha256()
    digest.update("\n".join(lines).encode("utf-8"))
    return digest.hexdigest()


def hash_entry(path: Path) -> tuple[str, str]:
    if path.is_dir():
        return "dir", hash_directory(path)
    if path.is_file():
        return "file", hash_file(path)
    raise FileNotFoundError(f"Update manifest target not found: {path}")


def build_update_manifest(
    package_root: Path,
    *,
    entry_names: Sequence[str] = DEFAULT_UPDATE_ENTRY_NAMES,
) -> dict[str, object]:
    package_root = package_root.resolve()
    version = _read_package_version(package_root / "version.json", label="version.json")
    entries: dict[str, dict[str, str]] = {}
    for entry_name in entry_names:
        entry_path = package_root / entry_name
        if not entry_path.exists():
            continue
        entry_type, sha256 = hash_entry(entry_path)
        entries[entry_name] = {"type": entry_type, "sha256": sha256}
    return {
        "manifestVersion": 1,
        "packageVersion": version,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }


def write_update_manifest(
    package_root: Path,
    *,
    entry_names: Sequence[str] = DEFAULT_UPDATE_ENTRY_NAMES,
) -> Path:
    package_root = package_root.resolve()
    manifest = build_update_manifest(package_root, entry_names=entry_names)
    manifest_path = package_root / "update-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
    return manifest_path


def validate_update_manifest(
    package_root: Path,
    *,
    expected_version: str,
    required_entries: Sequence[str],
) -> None:
    package_root = package_root.resolve()
    manifest_path = package_root / "update-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("更新包缺少 update-manifest.json。")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("更新包的 update-manifest.json 不是合法 JSON。") from exc

    manifest_version = str(manifest.get("packageVersion") or "").strip()
    if not manifest_version:
        raise ValueError("更新包的完整性清单缺少有效版本号。")
    if manifest_version != expected_version:
        raise ValueError("更新包版本信息与完整性清单不一致。")

    entries = manifest.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("更新包的完整性清单缺少有效 entries。")

    for entry_name in required_entries:
        record = entries.get(entry_name)
        if not isinstance(record, dict):
            raise ValueError(f"更新包缺少必要的完整性记录：{entry_name}")
        entry_path = package_root / entry_name
        if not entry_path.exists():
            raise ValueError(f"更新包完整性校验失败：{entry_name}")
        actual_type, actual_sha256 = hash_entry(entry_path)
        expected_type = str(record.get("type") or "").strip()
        expected_sha256 = str(record.get("sha256") or "").strip().lower()
        if actual_type != expected_type or actual_sha256 != expected_sha256:
            raise ValueError(f"更新包完整性校验失败：{entry_name}")


def _read_package_version(version_file: Path, *, label: str) -> str:
    try:
        payload = json.loads(version_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} 不是合法 JSON。") from exc
    version = str(payload.get("version") or "").strip()
    if not version:
        raise ValueError(f"{label} 缺少有效的版本号。")
    return version
