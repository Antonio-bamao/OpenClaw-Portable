import json
import os
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.services.update_manifest import build_update_manifest, hash_directory, validate_update_manifest, write_update_manifest


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"update-manifest-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def stage_package_root(root: Path) -> None:
    (root / "version.json").write_text(json.dumps({"version": "v2026.04.2"}), encoding="utf-8")
    (root / "OpenClawLauncher.exe").write_text("exe\n", encoding="utf-8")
    (root / "_internal" / "core.dll").parent.mkdir(parents=True, exist_ok=True)
    (root / "_internal" / "core.dll").write_text("dll\n", encoding="utf-8")
    (root / "runtime" / "openclaw" / "entry.mjs").parent.mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "openclaw" / "entry.mjs").write_text("runtime\n", encoding="utf-8")
    (root / "assets" / "logo.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "assets" / "logo.txt").write_text("asset\n", encoding="utf-8")
    (root / "tools" / "helper.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "tools" / "helper.txt").write_text("tool\n", encoding="utf-8")
    (root / "README.txt").write_text("readme\n", encoding="utf-8")


def long_path(path: Path) -> str:
    text = str(path)
    if os.name != "nt" or text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def write_text_long(path: Path, content: str) -> None:
    os.makedirs(long_path(path.parent), exist_ok=True)
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write(content)


class UpdateManifestTests(unittest.TestCase):
    def test_generates_manifest_with_expected_entries(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            stage_package_root(package_root)

            manifest = build_update_manifest(package_root)

            self.assertEqual(manifest["packageVersion"], "v2026.04.2")
            self.assertIn("runtime", manifest["entries"])
            self.assertIn("OpenClawLauncher.exe", manifest["entries"])
            self.assertEqual(manifest["entries"]["runtime"]["type"], "dir")
            self.assertEqual(manifest["entries"]["OpenClawLauncher.exe"]["type"], "file")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_directory_hash_changes_when_file_content_changes(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            directory = temp_dir / "runtime" / "openclaw"
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / "entry.mjs"
            target.write_text("version-one\n", encoding="utf-8")
            first_hash = hash_directory(directory)

            target.write_text("version-two\n", encoding="utf-8")
            second_hash = hash_directory(directory)

            self.assertNotEqual(first_hash, second_hash)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_write_update_manifest_persists_manifest_file(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            stage_package_root(package_root)

            manifest_path = write_update_manifest(package_root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest_path.name, "update-manifest.json")
            self.assertEqual(manifest["packageVersion"], "v2026.04.2")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_update_manifest_handles_long_runtime_paths(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            deep_runtime_file = Path(
                "runtime/openclaw/dist/extensions/discord/node_modules/@buape/carbon/"
                "node_modules/discord-api-types/payloads/v10/_interactions/"
                "_applicationCommands/_chatInput/attachment.js"
            )
            short_root = temp_dir / "s"
            long_root = (
                temp_dir
                / "system-temp"
                / "OpenClawPortable"
                / "updates"
                / "packages"
                / "v2026.04.3"
                / "OpenClaw-Portable"
            )
            write_text_long(short_root / "version.json", json.dumps({"version": "v2026.04.3"}))
            write_text_long(short_root / deep_runtime_file, "deep runtime\n")
            manifest_path = write_update_manifest(short_root)

            write_text_long(long_root / "version.json", json.dumps({"version": "v2026.04.3"}))
            write_text_long(long_root / deep_runtime_file, "deep runtime\n")
            write_text_long(long_root / "update-manifest.json", manifest_path.read_text(encoding="utf-8"))

            validate_update_manifest(long_root, expected_version="v2026.04.3", required_entries=["runtime", "version.json"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
