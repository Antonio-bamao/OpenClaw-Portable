from __future__ import annotations

import json
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.update_feed import resolve_update_feed_url


VERSION_PATTERN = re.compile(r"^v?(?P<core>\d+(?:\.\d+)*)(?:-(?P<suffix>[A-Za-z0-9.-]+))?$")


@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    latest_version: str
    notes: list[str]
    package_url: str


class OnlineUpdateService:
    def __init__(
        self,
        paths: PortablePaths,
        *,
        update_feed_url: str | None = None,
        fetch_text=None,
        fetch_bytes=None,
    ) -> None:
        self.paths = paths
        self.update_feed_url = resolve_update_feed_url(update_feed_url)
        self._fetch_text = fetch_text or self._default_fetch_text
        self._fetch_bytes = fetch_bytes or self._default_fetch_bytes

    def check_for_updates(self, current_version: str) -> UpdateCheckResult:
        try:
            payload = self._fetch_text(self.update_feed_url)
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise ValueError("当前无法连接更新服务器，请稍后再试。") from exc

        try:
            document = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("更新信息格式错误，请联系售后。") from exc

        version = str(document.get("version") or "").strip()
        package_url = str(document.get("packageUrl") or "").strip()
        notes_raw = document.get("notes") or []
        if not version or not package_url or not isinstance(notes_raw, list):
            raise ValueError("更新信息格式错误，请联系售后。")
        self._version_key(version)
        self._version_key(current_version)
        notes = [str(item).strip() for item in notes_raw if str(item).strip()]
        update_available = self._compare_versions(version, current_version) > 0
        return UpdateCheckResult(
            update_available=update_available,
            latest_version=version,
            notes=notes,
            package_url=package_url,
        )

    def download_update_package(self, metadata: UpdateCheckResult) -> Path:
        downloads_root = self.paths.temp_root / "updates" / "downloads"
        packages_root = self.paths.temp_root / "updates" / "packages"
        downloads_root.mkdir(parents=True, exist_ok=True)
        packages_root.mkdir(parents=True, exist_ok=True)
        archive_path = downloads_root / f"{metadata.latest_version}.zip"
        extract_root = packages_root / metadata.latest_version
        if extract_root.exists():
            shutil.rmtree(extract_root, ignore_errors=True)
        extract_root.mkdir(parents=True, exist_ok=True)

        try:
            archive_path.write_bytes(self._fetch_bytes(metadata.package_url))
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise ValueError("更新包下载失败，请检查网络后重试。") from exc

        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                self._extract_archive(archive, extract_root)
        except (zipfile.BadZipFile, OSError) as exc:
            raise ValueError("更新包解压失败，可能是下载不完整。") from exc

        package_root = self._locate_package_root(extract_root)
        if package_root is None:
            raise ValueError("更新包内容不完整，请重新下载。")
        return package_root

    def _locate_package_root(self, extract_root: Path) -> Path | None:
        candidates = [extract_root]
        candidates.extend(sorted(path for path in extract_root.iterdir() if path.is_dir()))
        for candidate in candidates:
            if (candidate / "version.json").exists() and (candidate / "update-manifest.json").exists():
                return candidate
        for candidate in sorted((path for path in extract_root.rglob("*") if path.is_dir()), key=lambda path: len(path.parts)):
            if (candidate / "version.json").exists() and (candidate / "update-manifest.json").exists():
                return candidate
        return None

    def _extract_archive(self, archive: zipfile.ZipFile, extract_root: Path) -> None:
        extract_root = extract_root.resolve()
        for item in archive.infolist():
            relative_path = Path(item.filename)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError("Update package contains an unsafe path.")
            target_path = extract_root / relative_path
            if item.is_dir():
                os.makedirs(self._long_path(target_path), exist_ok=True)
                continue
            os.makedirs(self._long_path(target_path.parent), exist_ok=True)
            with archive.open(item, "r") as source, open(self._long_path(target_path), "wb") as target:
                shutil.copyfileobj(source, target)

    def _long_path(self, path: Path) -> str:
        text = str(path)
        if os.name != "nt" or text.startswith("\\\\?\\"):
            return text
        if text.startswith("\\\\"):
            return "\\\\?\\UNC\\" + text.lstrip("\\")
        return "\\\\?\\" + text

    def _default_fetch_text(self, url: str) -> str:
        with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
            return response.read().decode("utf-8")

    def _default_fetch_bytes(self, url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            return response.read()

    def _compare_versions(self, left: str, right: str) -> int:
        left_core, left_stability, left_suffix = self._version_key(left)
        right_core, right_stability, right_suffix = self._version_key(right)
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

    def _version_key(self, version: str) -> tuple[tuple[int, ...], int, str]:
        match = VERSION_PATTERN.fullmatch(version.strip())
        if not match:
            raise ValueError("更新信息格式错误，请联系售后。")
        core = tuple(int(part) for part in match.group("core").split("."))
        suffix = (match.group("suffix") or "").strip()
        stability_rank = 1 if not suffix else 0
        return core, stability_rank, suffix
