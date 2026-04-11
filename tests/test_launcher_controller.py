import shutil
import socket
import time
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter
from launcher.services.controller import LauncherController


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"controller-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config(
    port: int = 18789,
    *,
    provider_id: str = "dashscope",
    provider_name: str = "通义千问",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    model: str = "qwen-max",
) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=base_url,
        model=model,
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


class LauncherControllerTests(unittest.TestCase):
    def test_defaults_to_mock_runtime_adapter(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            controller = LauncherController(make_paths(temp_dir), node_command="node")

            self.assertIsInstance(controller.runtime_adapter, MockRuntimeAdapter)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_can_select_real_openclaw_runtime_adapter(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            controller = LauncherController(make_paths(temp_dir), runtime_mode="openclaw", node_command="node")

            self.assertIsInstance(controller.runtime_adapter, OpenClawRuntimeAdapter)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_rejects_unknown_runtime_mode(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            with self.assertRaisesRegex(ValueError, "runtime_mode"):
                LauncherController(make_paths(temp_dir), runtime_mode="docker", node_command="node")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

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

    def test_view_state_labels_real_openclaw_runtime_mode(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            state = controller.load_view_state()

            self.assertEqual(state.runtime_detail, "OpenClaw gateway / v2026.4.8")
            self.assertIn("真实 OpenClaw", state.message)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_view_state_warns_when_real_openclaw_api_key_is_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            controller.configure(make_config(), SensitiveConfig(api_key=""))

            state = controller.load_view_state()

            self.assertTrue(state.offline_mode)
            self.assertIn("API Key", state.message)
            self.assertIn("重新配置", state.message)
            self.assertIn("通义千问", state.message)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_pending_start_view_state_warns_about_openclaw_startup_delay(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            config = make_config(reserve_free_port())
            controller.configure(config, SensitiveConfig(api_key="sk-demo"))

            state = controller.load_pending_runtime_view_state()

            self.assertEqual(state.status_label, "启动中")
            self.assertIn("20-90 秒", state.status_detail)
            self.assertIn("请勿关闭", state.message)
            self.assertEqual(state.port_label, f"127.0.0.1:{config.gateway_port}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_view_state_warns_when_custom_provider_config_is_incomplete(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            controller.configure(
                make_config(
                    provider_id="custom",
                    provider_name="自定义",
                    base_url="",
                    model="",
                ),
                SensitiveConfig(api_key="sk-demo"),
            )

            state = controller.load_view_state()

            self.assertIn("自定义 Provider", state.message)
            self.assertIn("接口地址", state.message)
            self.assertIn("模型名", state.message)
            self.assertIn("重新配置", state.message)
            self.assertEqual(state.provider_label, "自定义 / 待补充模型")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_pending_state_warns_before_start_when_custom_provider_config_is_incomplete(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            controller.configure(
                make_config(
                    port=reserve_free_port(),
                    provider_id="custom",
                    provider_name="自定义",
                    base_url="",
                    model="",
                ),
                SensitiveConfig(api_key="sk-demo"),
            )

            state = controller.load_pending_runtime_view_state()

            self.assertEqual(state.status_label, "启动中")
            self.assertIn("自定义 Provider", state.message)
            self.assertIn("接口地址", state.message)
            self.assertIn("重新配置", state.message)
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
            time.sleep(1.1)
            running = controller.load_view_state()

            self.assertEqual(running.status_label, "运行中")
            self.assertTrue(running.webui_url.startswith("http://127.0.0.1:"))
            self.assertIn("已运行", running.status_detail)

            controller.stop_runtime()
            stopped = controller.load_view_state()
            self.assertEqual(stopped.status_label, "已停止")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


    def test_reset_factory_state_returns_controller_to_first_run_but_keeps_workspace_and_backups(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            controller = LauncherController(paths, runtime_mode="openclaw", node_command="node")
            controller.configure(make_config(reserve_free_port()), SensitiveConfig(api_key="sk-demo"))
            paths.ensure_directories()
            (paths.workspace_dir / "notes.txt").write_text("keep me\n", encoding="utf-8")
            (paths.state_dir / "backups" / "support.zip").write_text("keep me too\n", encoding="utf-8")
            (paths.logs_dir / "openclaw-runtime.err.log").write_text("runtime failed\n", encoding="utf-8")

            controller.reset_factory_state()
            state = controller.load_view_state()

            self.assertTrue(controller.store.is_first_run())
            self.assertEqual(state.webui_url, "")
            self.assertTrue((paths.workspace_dir / "notes.txt").exists())
            self.assertTrue((paths.state_dir / "backups" / "support.zip").exists())
            self.assertFalse((paths.logs_dir / "openclaw-runtime.err.log").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
