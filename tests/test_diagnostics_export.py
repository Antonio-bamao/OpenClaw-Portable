import json
import shutil
import unittest
import uuid
import zipfile
from pathlib import Path

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.services.diagnostics_export import DiagnosticsExporter


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"diagnostics-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config() -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id="dashscope",
        provider_name="通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        gateway_port=18789,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


class DiagnosticsExporterTests(unittest.TestCase):
    def test_exports_redacted_bundle_with_version_and_logs(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            LauncherConfigStore(paths).save(make_config(), SensitiveConfig(api_key="sk-secret-demo"))
            (paths.project_root / "version.json").write_text(
                json.dumps({"version": "v2026.04.1-dev", "openclawVersion": "2026.4.8"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (paths.logs_dir / "openclaw-runtime.err.log").write_text("runtime failed\n", encoding="utf-8")

            bundle_path = DiagnosticsExporter(paths, runtime_mode="openclaw").export_bundle()

            self.assertTrue(bundle_path.exists())
            self.assertEqual(bundle_path.suffix, ".zip")
            self.assertEqual(bundle_path.parent, paths.state_dir / "backups")
            with zipfile.ZipFile(bundle_path) as archive:
                names = set(archive.namelist())
                self.assertIn("manifest.json", names)
                self.assertIn("config-summary.json", names)
                self.assertIn("version.json", names)
                self.assertIn("logs/openclaw-runtime.err.log", names)
                summary = json.loads(archive.read("config-summary.json").decode("utf-8"))
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

            self.assertEqual(summary["providerId"], "dashscope")
            self.assertEqual(summary["providerName"], "通义千问")
            self.assertTrue(summary["apiKeyConfigured"])
            self.assertTrue(summary["adminPasswordConfigured"])
            self.assertNotIn("apiKey", summary)
            self.assertNotIn("adminPassword", summary)
            self.assertEqual(manifest["runtimeMode"], "openclaw")
            self.assertEqual(manifest["logsIncluded"], ["openclaw-runtime.err.log"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_exports_bundle_even_before_first_run(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            (paths.project_root / "version.json").write_text('{"version":"v2026.04.1-dev"}', encoding="utf-8")

            bundle_path = DiagnosticsExporter(paths, runtime_mode="mock").export_bundle()

            with zipfile.ZipFile(bundle_path) as archive:
                summary = json.loads(archive.read("config-summary.json").decode("utf-8"))
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

            self.assertTrue(summary["firstRun"])
            self.assertFalse(summary["apiKeyConfigured"])
            self.assertEqual(manifest["runtimeMode"], "mock")
            self.assertEqual(manifest["logsIncluded"], [])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
