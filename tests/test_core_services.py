import json
import shutil
import socket
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.core.port_resolver import PortResolver


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"test-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class PortablePathsTests(unittest.TestCase):
    def test_builds_portable_directory_layout_from_project_root(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            root = temp_dir / "OpenClaw-Portable"
            paths = PortablePaths.for_root(root, temp_base=temp_dir / "system-temp")

            self.assertEqual(paths.project_root, root)
            self.assertEqual(paths.runtime_dir, root / "runtime")
            self.assertEqual(paths.state_dir, root / "state")
            self.assertEqual(paths.assets_dir, root / "assets")
            self.assertEqual(paths.tools_dir, root / "tools")
            self.assertEqual(paths.temp_root.name, "OpenClawPortable")
            self.assertEqual(paths.logs_dir, paths.temp_root / "logs")
            self.assertEqual(paths.cache_dir, paths.temp_root / "cache")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class LauncherConfigStoreTests(unittest.TestCase):
    def test_reports_first_run_when_config_does_not_exist(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            store = LauncherConfigStore(paths)

            self.assertTrue(store.is_first_run())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_persists_non_sensitive_config_to_json_and_sensitive_config_to_env(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            root = temp_dir / "OpenClaw-Portable"
            paths = PortablePaths.for_root(root, temp_base=temp_dir / "system-temp")
            store = LauncherConfigStore(paths)

            config = LauncherConfig(
                admin_password="demo-pass",
                provider_id="dashscope",
                provider_name="通义千问",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                model="qwen-max",
                gateway_port=18789,
                bind_host="127.0.0.1",
                first_run_completed=True,
            )
            sensitive = SensitiveConfig(api_key="sk-demo-key")

            store.save(config, sensitive)
            loaded_config, loaded_sensitive = store.load()

            raw_json = json.loads(paths.config_file.read_text(encoding="utf-8"))
            env_text = paths.env_file.read_text(encoding="utf-8")

            self.assertEqual(loaded_config.provider_id, "dashscope")
            self.assertEqual(loaded_sensitive.api_key, "sk-demo-key")
            self.assertNotIn("api_key", raw_json)
            self.assertIn("OPENCLAW_API_KEY=sk-demo-key", env_text)
            self.assertFalse(store.is_first_run())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class PortResolverTests(unittest.TestCase):
    def test_returns_current_port_when_available(self) -> None:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        available_port = probe.getsockname()[1]
        probe.close()

        resolution = PortResolver().resolve("127.0.0.1", available_port)

        self.assertEqual(resolution.port, available_port)
        self.assertIsNone(resolution.message)

    def test_moves_to_next_port_when_requested_port_is_occupied(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        occupied_port = server.getsockname()[1]

        try:
            resolution = PortResolver().resolve("127.0.0.1", occupied_port)
        finally:
            server.close()

        self.assertEqual(resolution.port, occupied_port + 1)
        self.assertIn(str(occupied_port + 1), resolution.message or "")
        self.assertIn("已自动切换", resolution.message or "")


if __name__ == "__main__":
    unittest.main()
