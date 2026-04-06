import shutil
import socket
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.mock_runtime import MockRuntimeAdapter


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"runtime-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_config(port: int) -> LauncherConfig:
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


def reserve_free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def stage_mock_runtime(paths: PortablePaths) -> None:
    paths.ensure_directories()
    source = Path.cwd() / "runtime" / "mock-runtime" / "server.js"
    target = paths.runtime_dir / "mock-runtime" / "server.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


class MockRuntimeAdapterTests(unittest.TestCase):
    def test_starts_runtime_and_reports_health(self) -> None:
        temp_dir = make_workspace_temp_dir()
        paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
        adapter = MockRuntimeAdapter(node_command="node")

        try:
            stage_mock_runtime(paths)
            adapter.prepare(make_config(reserve_free_port()), paths)
            adapter.start()

            status = adapter.status()
            health = adapter.healthcheck()

            self.assertEqual(status.state, "running")
            self.assertTrue(health.ok)
            self.assertEqual(adapter.webui_url(), f"http://127.0.0.1:{status.port}")
        finally:
            adapter.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_switches_to_next_port_when_requested_one_is_busy(self) -> None:
        temp_dir = make_workspace_temp_dir()
        paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
        adapter = MockRuntimeAdapter(node_command="node")
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        occupied_port = blocker.getsockname()[1]

        try:
            stage_mock_runtime(paths)
            adapter.prepare(make_config(occupied_port), paths)
            adapter.start()
            status = adapter.status()

            self.assertEqual(status.state, "running")
            self.assertEqual(status.port, occupied_port + 1)
            self.assertIn("已自动切换", status.message or "")
        finally:
            blocker.close()
            adapter.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
