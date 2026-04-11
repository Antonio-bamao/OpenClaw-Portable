import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.local_update import LocalUpdateImportService, RestoreUpdateBackupService
from launcher.services.update_manifest import write_update_manifest
from launcher.services.update_signature import DEFAULT_UPDATE_SIGNING_KEY_ID, generate_update_signing_keypair, write_update_signature


TEST_PRIVATE_KEY_B64, TEST_PUBLIC_KEY_B64 = generate_update_signing_keypair()
SECONDARY_TEST_PRIVATE_KEY_B64, SECONDARY_TEST_PUBLIC_KEY_B64 = generate_update_signing_keypair()


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"local-update-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_import_service(paths: PortablePaths) -> LocalUpdateImportService:
    return LocalUpdateImportService(
        paths,
        signature_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
        signature_public_key_b64=TEST_PUBLIC_KEY_B64,
    )


def make_rotating_import_service(paths: PortablePaths) -> LocalUpdateImportService:
    return LocalUpdateImportService(
        paths,
        signature_public_keys={
            DEFAULT_UPDATE_SIGNING_KEY_ID: TEST_PUBLIC_KEY_B64,
            "portable-ed25519-v2": SECONDARY_TEST_PUBLIC_KEY_B64,
        },
    )


def stage_target_portable(paths: PortablePaths, *, version: str = "v1", label: str = "old") -> None:
    paths.ensure_directories()
    (paths.project_root / "version.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    (paths.project_root / "README.txt").write_text(f"{label} readme\n", encoding="utf-8")
    (paths.project_root / "OpenClawLauncher.exe").write_text(f"{label} exe\n", encoding="utf-8")
    (paths.project_root / "_internal").mkdir(parents=True, exist_ok=True)
    (paths.project_root / "_internal" / "core.dll").write_text(f"{label} dll\n", encoding="utf-8")
    (paths.runtime_dir / "openclaw").mkdir(parents=True, exist_ok=True)
    (paths.runtime_dir / "openclaw" / "openclaw.mjs").write_text(f"{label} runtime\n", encoding="utf-8")
    (paths.assets_dir / "logo.txt").write_text(f"{label} asset\n", encoding="utf-8")
    (paths.tools_dir / "helper.txt").write_text(f"{label} tool\n", encoding="utf-8")
    (paths.state_dir / "openclaw.json").write_text("keep state\n", encoding="utf-8")
    (paths.state_dir / ".env").write_text("OPENCLAW_API_KEY=keep\n", encoding="utf-8")


def stage_source_package(root: Path, *, version: str = "v2", label: str = "new") -> None:
    (root / "version.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    (root / "README.txt").write_text(f"{label} readme\n", encoding="utf-8")
    (root / "OpenClawLauncher.exe").write_text(f"{label} exe\n", encoding="utf-8")
    (root / "_internal").mkdir(parents=True, exist_ok=True)
    (root / "_internal" / "core.dll").write_text(f"{label} dll\n", encoding="utf-8")
    (root / "runtime" / "openclaw").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "openclaw" / "openclaw.mjs").write_text(f"{label} runtime\n", encoding="utf-8")
    (root / "assets" / "logo.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "assets" / "logo.txt").write_text(f"{label} asset\n", encoding="utf-8")
    (root / "tools" / "helper.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "tools" / "helper.txt").write_text(f"{label} tool\n", encoding="utf-8")
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "state" / "openclaw.json").write_text("must not copy\n", encoding="utf-8")


def finalize_source_package(root: Path) -> None:
    write_update_manifest(root)


def finalize_signed_source_package(root: Path) -> None:
    write_update_manifest(root)
    write_update_signature(root, private_key_b64=TEST_PRIVATE_KEY_B64)


def finalize_secondary_signed_source_package(root: Path) -> None:
    write_update_manifest(root)
    write_update_signature(
        root,
        private_key_b64=SECONDARY_TEST_PRIVATE_KEY_B64,
        key_id="portable-ed25519-v2",
    )


def stage_version_only_package(root: Path, version: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "version.json").write_text(json.dumps({"version": version}), encoding="utf-8")


class FailingLocalUpdateImportService(LocalUpdateImportService):
    def _copy_entry(self, source: Path, destination: Path) -> None:
        if source.name == "tools":
            raise RuntimeError("simulated copy failure")
        super()._copy_entry(source, destination)


class FailingRestoreUpdateBackupService(RestoreUpdateBackupService):
    def __init__(self, paths: PortablePaths) -> None:
        super().__init__(paths)
        self._has_failed = False

    def _copy_entry(self, source: Path, destination: Path) -> None:
        if not self._has_failed and source.name == "tools" and destination == self.paths.project_root / "tools":
            self._has_failed = True
            raise RuntimeError("simulated restore failure")
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
            finalize_signed_source_package(source_root)

            result = make_import_service(paths).import_package(source_root)

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
            finalize_signed_source_package(source_root)

            with self.assertRaisesRegex(RuntimeError, "simulated copy failure"):
                FailingLocalUpdateImportService(
                    paths,
                    signature_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
                    signature_public_key_b64=TEST_PUBLIC_KEY_B64,
                ).import_package(source_root)

            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "old readme\n")
            self.assertEqual((paths.project_root / "OpenClawLauncher.exe").read_text(encoding="utf-8"), "old exe\n")
            self.assertEqual((paths.project_root / "_internal" / "core.dll").read_text(encoding="utf-8"), "old dll\n")
            self.assertEqual((paths.runtime_dir / "openclaw" / "openclaw.mjs").read_text(encoding="utf-8"), "old runtime\n")
            self.assertEqual((paths.tools_dir / "helper.txt").read_text(encoding="utf-8"), "old tool\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_package_with_invalid_version_json(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1-dev")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            (source_root / "version.json").write_text("{bad json", encoding="utf-8")
            (source_root / "runtime" / "openclaw").mkdir(parents=True, exist_ok=True)
            (source_root / "runtime" / "openclaw" / "openclaw.mjs").write_text("new runtime\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "version.json"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_package_without_distribution_entries(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1-dev")
            source_root = temp_dir / "incoming-package"
            stage_version_only_package(source_root, "v2026.04.2")

            with self.assertRaisesRegex(FileNotFoundError, "程序文件"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_same_version_package(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.2")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="same")
            finalize_signed_source_package(source_root)

            with self.assertRaisesRegex(ValueError, "重复导入"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_older_version_package_and_guides_restore_flow(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.2")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.1", label="older")
            finalize_signed_source_package(source_root)

            with self.assertRaisesRegex(ValueError, "恢复更新备份"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_release_version_is_newer_than_same_dev_version(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1-dev", label="dev")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.1", label="release")
            finalize_signed_source_package(source_root)

            result = make_import_service(paths).import_package(source_root)

            self.assertEqual(result.imported_version, "v2026.04.1")
            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "release readme\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_imports_package_signed_by_secondary_trusted_key(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1", label="old")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            finalize_secondary_signed_source_package(source_root)

            result = make_rotating_import_service(paths).import_package(source_root)

            self.assertEqual(result.imported_version, "v2026.04.2")
            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "new readme\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_restores_distribution_content_from_backup_without_overwriting_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2", label="current")
            backup_root = paths.state_dir / "backups" / "updates" / "20260411-120000"
            backup_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(backup_root, version="v1", label="restored")
            finalize_source_package(backup_root)

            result = RestoreUpdateBackupService(paths).restore_backup(backup_root)

            self.assertEqual(result.restored_version, "v1")
            self.assertEqual(result.source_backup_dir, backup_root.resolve())
            self.assertTrue(result.backup_dir.exists())
            self.assertIn("runtime", result.restored_entries)
            self.assertEqual((paths.project_root / "version.json").read_text(encoding="utf-8"), json.dumps({"version": "v1"}))
            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "restored readme\n")
            self.assertEqual((paths.project_root / "OpenClawLauncher.exe").read_text(encoding="utf-8"), "restored exe\n")
            self.assertEqual((paths.project_root / "_internal" / "core.dll").read_text(encoding="utf-8"), "restored dll\n")
            self.assertEqual((paths.runtime_dir / "openclaw" / "openclaw.mjs").read_text(encoding="utf-8"), "restored runtime\n")
            self.assertEqual((paths.state_dir / "openclaw.json").read_text(encoding="utf-8"), "keep state\n")
            self.assertEqual((paths.state_dir / ".env").read_text(encoding="utf-8"), "OPENCLAW_API_KEY=keep\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_restore_rolls_back_when_copy_fails_mid_restore(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2", label="current")
            backup_root = paths.state_dir / "backups" / "updates" / "20260411-120000"
            backup_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(backup_root, version="v1", label="restored")
            finalize_source_package(backup_root)

            with self.assertRaisesRegex(RuntimeError, "simulated restore failure"):
                FailingRestoreUpdateBackupService(paths).restore_backup(backup_root)

            self.assertEqual((paths.project_root / "README.txt").read_text(encoding="utf-8"), "current readme\n")
            self.assertEqual((paths.project_root / "OpenClawLauncher.exe").read_text(encoding="utf-8"), "current exe\n")
            self.assertEqual((paths.project_root / "_internal" / "core.dll").read_text(encoding="utf-8"), "current dll\n")
            self.assertEqual((paths.runtime_dir / "openclaw" / "openclaw.mjs").read_text(encoding="utf-8"), "current runtime\n")
            self.assertEqual((paths.tools_dir / "helper.txt").read_text(encoding="utf-8"), "current tool\n")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_restore_requires_at_least_one_distribution_entry(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2", label="current")
            backup_root = paths.state_dir / "backups" / "updates" / "20260411-120000"
            backup_root.mkdir(parents=True, exist_ok=True)

            with self.assertRaisesRegex(FileNotFoundError, "分发内容"):
                RestoreUpdateBackupService(paths).restore_backup(backup_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_without_manifest(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")

            with self.assertRaisesRegex(FileNotFoundError, "update-manifest.json"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_without_signature(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            write_update_manifest(source_root)

            with self.assertRaisesRegex(FileNotFoundError, "update-signature.json"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_when_manifest_version_mismatches_version_json(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            manifest_path = write_update_manifest(source_root)
            write_update_signature(source_root, private_key_b64=TEST_PRIVATE_KEY_B64)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["packageVersion"] = "v2026.04.3"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "数字签名校验失败|完整性清单"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_when_signature_does_not_match_manifest(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            finalize_signed_source_package(source_root)
            manifest_path = source_root / "update-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generatedAt"] = "2026-04-11T12:34:56+00:00"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "数字签名校验失败"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_when_manifest_hash_does_not_match(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            finalize_signed_source_package(source_root)
            (source_root / "README.txt").write_text("tampered readme\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "数字签名校验失败|完整性校验失败"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_update_package_when_manifest_lacks_entry_record(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_target_portable(paths, version="v2026.04.1")
            source_root = temp_dir / "incoming-package"
            source_root.mkdir(parents=True, exist_ok=True)
            stage_source_package(source_root, version="v2026.04.2", label="new")
            manifest_path = write_update_manifest(source_root)
            write_update_signature(source_root, private_key_b64=TEST_PRIVATE_KEY_B64)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["entries"]["runtime"]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "数字签名校验失败|缺少必要的完整性记录"):
                make_import_service(paths).import_package(source_root)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
