import json
import shutil
import unittest
import uuid
import zipfile
from pathlib import Path

from launcher.services.release_assets import (
    build_release_asset_name,
    build_release_package_url,
    build_release_update_document,
    build_release_assets,
)
from launcher.services.update_signature import generate_update_signing_keypair, write_update_signature


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"release-assets-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class ReleaseAssetsTests(unittest.TestCase):
    def test_build_release_asset_name_uses_version(self) -> None:
        self.assertEqual(build_release_asset_name("v2026.04.2"), "OpenClaw-Portable-v2026.04.2.zip")

    def test_build_release_package_url_targets_release_tag_asset(self) -> None:
        self.assertEqual(
            build_release_package_url("Antonio-bamao/OpenClaw-Portable", "v2026.04.2"),
            "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.2/OpenClaw-Portable-v2026.04.2.zip",
        )

    def test_build_release_update_document_contains_expected_fields(self) -> None:
        document = build_release_update_document(
            version="v2026.04.2",
            repository="Antonio-bamao/OpenClaw-Portable",
            notes=["note a"],
        )

        self.assertEqual(document["version"], "v2026.04.2")
        self.assertEqual(document["notes"], ["note a"])
        self.assertEqual(
            document["packageUrl"],
            "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.2/OpenClaw-Portable-v2026.04.2.zip",
        )

    def test_build_release_assets_creates_zip_and_update_json(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            output_dir = temp_dir / "release"
            package_root.mkdir(parents=True, exist_ok=True)
            (package_root / "version.json").write_text(json.dumps({"version": "v2026.04.2"}), encoding="utf-8")
            (package_root / "update-manifest.json").write_text(json.dumps({"manifestVersion": 1}), encoding="utf-8")
            (package_root / "README.txt").write_text("hello", encoding="utf-8")
            private_key_b64, _ = generate_update_signing_keypair()
            write_update_signature(package_root, private_key_b64=private_key_b64)

            archive_path, update_json_path = build_release_assets(
                package_root=package_root,
                output_dir=output_dir,
                repository="Antonio-bamao/OpenClaw-Portable",
                notes=["note a"],
            )

            self.assertTrue(archive_path.exists())
            self.assertEqual(archive_path.name, "OpenClaw-Portable-v2026.04.2.zip")
            with zipfile.ZipFile(archive_path, "r") as archive:
                self.assertIn("OpenClaw-Portable/version.json", archive.namelist())
                self.assertIn("OpenClaw-Portable/update-manifest.json", archive.namelist())
                self.assertIn("OpenClaw-Portable/update-signature.json", archive.namelist())

            self.assertTrue(update_json_path.exists())
            document = json.loads(update_json_path.read_text(encoding="utf-8"))
            self.assertEqual(document["version"], "v2026.04.2")
            self.assertEqual(document["notes"], ["note a"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_release_assets_rejects_mutable_state_entries(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            output_dir = temp_dir / "release"
            package_root.mkdir(parents=True, exist_ok=True)
            (package_root / "version.json").write_text(json.dumps({"version": "v2026.04.2"}), encoding="utf-8")
            (package_root / "update-manifest.json").write_text(json.dumps({"manifestVersion": 1}), encoding="utf-8")
            private_key_b64, _ = generate_update_signing_keypair()
            write_update_signature(package_root, private_key_b64=private_key_b64)
            (package_root / "state" / "provider-templates" / "qwen.json").parent.mkdir(parents=True, exist_ok=True)
            (package_root / "state" / "provider-templates" / "qwen.json").write_text("{}", encoding="utf-8")
            (package_root / "state" / "openclaw.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "mutable state entries"):
                build_release_assets(
                    package_root=package_root,
                    output_dir=output_dir,
                    repository="Antonio-bamao/OpenClaw-Portable",
                    notes=["note a"],
                )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
