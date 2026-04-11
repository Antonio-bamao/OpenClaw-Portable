import io
import json
import os
import shutil
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from launcher.core.paths import PortablePaths
from launcher.services.online_update import OnlineUpdateService
from launcher.services.update_feed import DEFAULT_UPDATE_FEED_URL


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"online-update-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_update_json(version: str = "v2026.04.2", package_url: str = "https://example.com/OpenClaw-Portable-v2026.04.2.zip") -> str:
    return json.dumps(
        {
            "version": version,
            "notes": ["升级到新的 OpenClaw runtime"],
            "packageUrl": package_url,
        },
        ensure_ascii=False,
    )


def make_package_zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("OpenClaw-Portable/version.json", json.dumps({"version": "v2026.04.2"}))
        archive.writestr(
            "OpenClaw-Portable/update-manifest.json",
            json.dumps(
                {
                    "manifestVersion": 1,
                    "packageVersion": "v2026.04.2",
                    "generatedAt": "2026-04-11T00:00:00+00:00",
                    "entries": {},
                }
            ),
        )
    return buffer.getvalue()


class OnlineUpdateServiceTests(unittest.TestCase):
    def test_online_update_service_uses_resolved_feed_url_when_no_explicit_url_is_passed(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OPENCLAW_PORTABLE_UPDATE_FEED_URL", None)
                service = OnlineUpdateService(make_paths(temp_dir))

            self.assertEqual(service.update_feed_url, DEFAULT_UPDATE_FEED_URL)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_online_update_service_prefers_environment_override_when_present(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            with patch.dict(os.environ, {"OPENCLAW_PORTABLE_UPDATE_FEED_URL": "https://staging.example.com/update.json"}, clear=False):
                service = OnlineUpdateService(make_paths(temp_dir))

            self.assertEqual(service.update_feed_url, "https://staging.example.com/update.json")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_check_update_returns_update_available_when_remote_version_is_newer(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_text=lambda _: make_update_json(),
            )

            result = service.check_for_updates("v2026.04.1")

            self.assertTrue(result.update_available)
            self.assertEqual(result.latest_version, "v2026.04.2")
            self.assertIn("升级到新的 OpenClaw runtime", result.notes)
            self.assertEqual(result.package_url, "https://example.com/OpenClaw-Portable-v2026.04.2.zip")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_check_update_returns_no_update_when_current_version_is_latest(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_text=lambda _: make_update_json(version="v2026.04.1"),
            )

            result = service.check_for_updates("v2026.04.1")

            self.assertFalse(result.update_available)
            self.assertEqual(result.latest_version, "v2026.04.1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_check_update_rejects_invalid_update_json(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_text=lambda _: "{bad json",
            )

            with self.assertRaisesRegex(ValueError, "更新信息格式错误"):
                service.check_for_updates("v2026.04.1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_check_update_rejects_missing_required_fields(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_text=lambda _: json.dumps({"version": "v2026.04.2"}),
            )

            with self.assertRaisesRegex(ValueError, "更新信息格式错误"):
                service.check_for_updates("v2026.04.1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_download_update_package_downloads_and_extracts_zip_to_temp_package_dir(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_bytes=lambda _: make_package_zip_bytes(),
            )
            metadata = service.check_for_updates("v2026.04.1") if False else None
            metadata = type("Metadata", (), {"latest_version": "v2026.04.2", "package_url": "https://example.com/pkg.zip"})()

            package_dir = service.download_update_package(metadata)

            self.assertTrue((package_dir / "version.json").exists())
            self.assertTrue((package_dir / "update-manifest.json").exists())
            self.assertIn("updates", str(package_dir))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_download_update_package_rejects_invalid_zip(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            service = OnlineUpdateService(
                make_paths(temp_dir),
                update_feed_url="https://example.com/update.json",
                fetch_bytes=lambda _: b"not-a-zip",
            )
            metadata = type("Metadata", (), {"latest_version": "v2026.04.2", "package_url": "https://example.com/pkg.zip"})()

            with self.assertRaisesRegex(ValueError, "解压失败"):
                service.download_update_package(metadata)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
