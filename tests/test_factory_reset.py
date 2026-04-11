import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.services.factory_reset import FactoryResetService


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"factory-reset-{uuid.uuid4().hex[:8]}"
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


class FactoryResetServiceTests(unittest.TestCase):
    def test_resets_launcher_config_and_temp_state_but_keeps_workspace_and_backups(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            LauncherConfigStore(paths).save(make_config(), SensitiveConfig(api_key="sk-demo"))
            (paths.provider_templates_dir / "custom.json").write_text("{}", encoding="utf-8")
            (paths.logs_dir / "openclaw-runtime.err.log").write_text("runtime failed\n", encoding="utf-8")
            (paths.cache_dir / "cache.bin").write_text("cached\n", encoding="utf-8")
            (paths.state_dir / "sessions" / "session.json").write_text("{}", encoding="utf-8")
            (paths.state_dir / "channels" / "channel.json").write_text("{}", encoding="utf-8")
            (paths.workspace_dir / "notes.txt").write_text("keep me\n", encoding="utf-8")
            (paths.state_dir / "backups" / "support.zip").write_text("keep me too\n", encoding="utf-8")
            (paths.runtime_dir / "openclaw" / "package.json").parent.mkdir(parents=True, exist_ok=True)
            (paths.runtime_dir / "openclaw" / "package.json").write_text("{}", encoding="utf-8")

            FactoryResetService(paths).reset()

            self.assertFalse(paths.config_file.exists())
            self.assertFalse(paths.env_file.exists())
            self.assertFalse((paths.provider_templates_dir / "custom.json").exists())
            self.assertFalse((paths.logs_dir / "openclaw-runtime.err.log").exists())
            self.assertFalse((paths.cache_dir / "cache.bin").exists())
            self.assertFalse((paths.state_dir / "sessions" / "session.json").exists())
            self.assertFalse((paths.state_dir / "channels" / "channel.json").exists())
            self.assertTrue((paths.workspace_dir / "notes.txt").exists())
            self.assertTrue((paths.state_dir / "backups" / "support.zip").exists())
            self.assertTrue((paths.runtime_dir / "openclaw" / "package.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_reset_is_safe_to_run_before_first_setup(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()

            FactoryResetService(paths).reset()

            self.assertFalse(paths.config_file.exists())
            self.assertFalse(paths.env_file.exists())
            self.assertTrue(paths.workspace_dir.exists())
            self.assertTrue((paths.state_dir / "backups").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
