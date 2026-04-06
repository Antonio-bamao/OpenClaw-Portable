import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.services.controller import LauncherController


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"controller-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config(port: int = 18789) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id="dashscope",
        provider_name="通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        gateway_port=port,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


def stage_mock_runtime(paths: PortablePaths) -> None:
    paths.ensure_directories()
    source = Path.cwd() / "runtime" / "mock-runtime" / "server.js"
    target = paths.runtime_dir / "mock-runtime" / "server.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


class LauncherControllerTests(unittest.TestCase):
    def test_loads_default_view_state_before_runtime_starts(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, node_command="node")
            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            state = controller.load_view_state()

            self.assertEqual(state.status_label, "已就绪")
            self.assertIn("通义千问", state.provider_label)
            self.assertIn("127.0.0.1", state.port_label)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_starts_and_stops_runtime_through_controller(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            stage_mock_runtime(paths)
            controller = LauncherController(paths, node_command="node")
            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            controller.start_runtime()
            running = controller.load_view_state()

            self.assertEqual(running.status_label, "运行中")
            self.assertTrue(running.webui_url.startswith("http://127.0.0.1:"))

            controller.stop_runtime()
            stopped = controller.load_view_state()
            self.assertEqual(stopped.status_label, "已停止")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
