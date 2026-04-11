import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.local_update import LocalUpdateImportService


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"local-update-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def stage_target_portable(paths: PortablePaths) -> None:
    paths.ensure_directories()
    (paths.project_root / "version.json").write_text(json.dumps({"version": "v1"}), encoding="utf-8")
    (paths.project_root / "README.txt").write_text("old readme\n", encoding="utf-8")
    (paths.project_root / "OpenClawLauncher.exe").write_text("old exe\n", encoding="utf-8")
    (paths.project_root / "_internal").mkdir(parents=True, exist_ok=True)
    (paths.project_root / "_internal" / "core.dll").write_text("old dll\n", encoding="utf-8")
    (paths.runtime_dir / "openclaw").mkdir(parents=True, exist_ok=True)
    (paths.runtime_dir / "openclaw" / "openclaw.mjs").write_text("old runtime\n", encoding="utf-8")
    (paths.assets_dir / "logo.txt").write_text("old asset\n", encoding="utf-8")
    (paths.tools_dir / "helper.txt").write_text("old tool\n", encoding="utf-8")
    (paths.state_dir / "openclaw.json").write_text("keep state\n", encoding="utf-8")
    (paths.state_dir / ".env").write_text("OPENCLAW_API_KEY=keep\n", encoding="utf-8")


def stage_source_package(root: Path) -> None:
    (root / "version.json").write_text(json.dumps({"version": "v2"}), encoding="utf-8")
    (root / "README.txt").write_text("new readme\n", encoding="utf-8")
    (root / "OpenClawLauncher.exe").write_text("new exe\n", encoding="utf-8")
    (root / "_internal").mkdir(parents=True, exist_ok=True)
    (root / "_internal" / "core.dll").write_text("new dll\n", encoding="utf-8")
    (root / "runtime" / "openclaw").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "openclaw" / "openclaw.mjs").write_text("new runtime\n", encoding="utf-8")
    (root / "assets" / "logo.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "assets" / "logo.txt").write_text("new asset\n", encoding="utf-8")
    (root / "tools" / "helper.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "tools" / "helper.txt").write_text("new tool\n", encoding="utf-8")
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "state" / "openclaw.json").write_text("must not copy\n", encoding="utf-8")


class FailingLocalUpdateImportService(LocalUpdateImportService):
    def _copy_entry(self, source: Path, destination: Path) -> None:
        if source.name == "tools":
            raise RuntimeError("simulated copy failure")
        super()._copy_entry(source, destination)


class LocalUpdateImportServiceTests(unittest.TestCase):
    def test_imports_distribution_content_without_overwriting_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths)
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root)

            result = LocalUpdateImportService(paths).import_package(source_root)

            self.assertEqual(result.imported_version, "v2")
            self.assertTrue(result.backup_dir.exists())
            self.assertIn("runtime", result.updated_entries)
            self.assertEqual((paths.project_root / "version.json").read_text(encoding="utf-8"), json.dumps({"version": "v2"}))
            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "new readme\n")
            self.assertEqual((paths.project_root / "OpenClawLauncher.exe").read_text(encoding="utf-8"), "new exe\n")
            self.assertEqual((paths.project_root / "_internal" / "core.dll").read_text(encoding="utf-8"), "new dll\n")
            self.assertEqual((paths.runtime_dir / "openclaw" / "openclaw.mjs").read_text(encoding="utf-8"), "new runtime\n")
            self.assertEqual((paths.state_dir / "openclaw.json").read_text(encoding="utf-8"), "keep state\n")
            self.assertEqual((paths.state_dir / ".env").read_text(encoding="utf-8"), "OPENCLAW_API_KEY=keep\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rolls_back_when_copy_fails_mid_update(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths)
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root)

            with self.assertRaisesRegex(RuntimeError, "simulated copy failure"):
                FailingLocalUpdateImportService(paths).import_package(source_root)

            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "old readme\n")
            self.assertEqual((paths.project_root / "OpenClawLauncher.exe").read_text(encoding="utf-8"), "old exe\n")
            self.assertEqual((paths.project_root / "_internal" / "core.dll").read_text(encoding="utf-8"), "old dll\n")
            self.assertEqual((paths.runtime_dir / "openclaw" / "openclaw.mjs").read_text(encoding="utf-8"), "old runtime\n")
            self.assertEqual((paths.tools_dir / "helper.txt").read_text(encoding="utf-8"), "old tool\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
