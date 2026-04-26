from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

from launcher.services.portable_audit import assert_release_state_clean


DEFAULT_RELEASE_REPOSITORY = "Antonio-bamao/OpenClaw-Portable"
LATEST_RELEASE_UPDATE_JSON_NAME = "update.json"


def build_latest_release_feed_url(repository: str = DEFAULT_RELEASE_REPOSITORY) -> str:
    repository = repository.strip()
    if not repository:
        raise ValueError("Release repository cannot be empty.")
    return f"https://github.com/{repository}/releases/latest/download/{LATEST_RELEASE_UPDATE_JSON_NAME}"


def build_release_asset_name(version: str) -> str:
    normalized_version = version.strip()
    if not normalized_version:
        raise ValueError("Release version cannot be empty.")
    return f"OpenClaw-Portable-{normalized_version}.zip"


def build_release_package_url(repository: str, version: str) -> str:
    normalized_repository = repository.strip()
    if not normalized_repository:
        raise ValueError("Release repository cannot be empty.")
    return f"https://github.com/{normalized_repository}/releases/download/{version}/{build_release_asset_name(version)}"


def build_release_update_document(*, version: str, repository: str, notes: list[str] | None = None) -> dict[str, object]:
    normalized_version = version.strip()
    if not normalized_version:
        raise ValueError("Release version cannot be empty.")
    normalized_notes = [str(note).strip() for note in (notes or []) if str(note).strip()]
    return {
        "version": normalized_version,
        "notes": normalized_notes,
        "packageUrl": build_release_package_url(repository, normalized_version),
    }


def write_release_update_json(*, version: str, repository: str, notes: list[str] | None = None, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = build_release_update_document(version=version, repository=repository, notes=notes)
    output_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def create_release_zip(package_root: Path, output_dir: Path) -> Path:
    version = read_package_version(package_root)
    if not (package_root / "update-signature.json").exists():
        raise FileNotFoundError("Portable package is missing update-signature.json.")
    assert_release_state_clean(package_root)
    archive_path = output_dir / build_release_asset_name(version)
    output_dir.mkdir(parents=True, exist_ok=True)
    root_name = package_root.name
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _iter_files(package_root):
            archive.write(_long_path(path), Path(root_name) / path.relative_to(package_root))
    return archive_path


def build_release_assets(*, package_root: Path, output_dir: Path, repository: str, notes: list[str] | None = None) -> tuple[Path, Path]:
    version = read_package_version(package_root)
    archive_path = create_release_zip(package_root, output_dir)
    update_json_path = write_release_update_json(
        version=version,
        repository=repository,
        notes=notes,
        output_path=output_dir / LATEST_RELEASE_UPDATE_JSON_NAME,
    )
    return archive_path, update_json_path


def read_package_version(package_root: Path) -> str:
    version_file = package_root / "version.json"
    if not version_file.exists():
        raise FileNotFoundError("Portable package is missing version.json.")
    try:
        document = json.loads(version_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Portable package version.json is not valid JSON.") from exc
    version = str(document.get("version") or "").strip()
    if not version:
        raise ValueError("Portable package version.json is missing version.")
    return version


def _iter_files(root: Path) -> list[Path]:
    if os.name != "nt":
        return sorted(item for item in root.rglob("*") if item.is_file())

    root = root.resolve()
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(_long_path(root)):
        for filename in filenames:
            files.append(Path(_strip_long_path(os.path.join(dirpath, filename))))
    return sorted(files)


def _long_path(path: Path) -> str:
    text = str(path)
    if os.name != "nt" or text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def _strip_long_path(path: str) -> str:
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path.removeprefix("\\\\?\\UNC\\")
    if path.startswith("\\\\?\\"):
        return path.removeprefix("\\\\?\\")
    return path
