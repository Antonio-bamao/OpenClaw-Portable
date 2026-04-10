import os
import shutil
import socket
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"openclaw-runtime-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


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


def reserve_free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


class OpenClawRuntimeAdapterTests(unittest.TestCase):
    def test_defaults_to_90_second_startup_timeout_for_real_runtime(self) -> None:
        adapter = OpenClawRuntimeAdapter()

        self.assertEqual(adapter.startup_timeout_seconds, 90)

    def test_start_fails_clearly_when_openclaw_runtime_is_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(), paths)

            with self.assertRaisesRegex(FileNotFoundError, "runtime.openclaw"):
                adapter.start()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prefers_embedded_node_when_it_exists(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            embedded_node = paths.runtime_dir / "node" / "node.exe"
            embedded_node.parent.mkdir(parents=True, exist_ok=True)
            embedded_node.write_text("", encoding="utf-8")

            adapter = OpenClawRuntimeAdapter(node_command="node")
            adapter.prepare(make_config(), paths)

            self.assertEqual(adapter.resolved_node_command(), str(embedded_node))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_builds_portable_environment_without_dropping_system_environment(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            paths.ensure_directories()
            paths.env_file.write_text("OPENCLAW_API_KEY=sk-demo\n", encoding="utf-8")
            config = make_config(reserve_free_port())
            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(config, paths)

            environment = adapter.build_environment()

            self.assertEqual(environment["OPENCLAW_GATEWAY_PORT"], str(config.gateway_port))
            self.assertEqual(environment["OPENCLAW_BIND_HOST"], "127.0.0.1")
            self.assertEqual(environment["OPENCLAW_HOME"], str(paths.state_dir))
            self.assertEqual(environment["HOME"], str(paths.state_dir))
            self.assertEqual(environment["OPENCLAW_STATE_DIR"], str(paths.state_dir))
            self.assertEqual(environment["OPENCLAW_CONFIG_PATH"], str(paths.config_file))
            self.assertEqual(environment["OPENCLAW_LOG_DIR"], str(paths.logs_dir))
            self.assertEqual(environment["OPENCLAW_CACHE_DIR"], str(paths.cache_dir))
            self.assertEqual(environment["OPENCLAW_API_KEY"], "sk-demo")
            self.assertEqual(environment.get("PATH"), os.environ.get("PATH"))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_webui_url_uses_resolved_port_after_prepare(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            adapter = OpenClawRuntimeAdapter()
            config = make_config(reserve_free_port())
            entrypoint = paths.runtime_dir / "openclaw" / "openclaw.mjs"
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text("#!/usr/bin/env node\n", encoding="utf-8")

            adapter.prepare(config, paths)

            self.assertEqual(adapter.status().state, "ready")
            self.assertEqual(adapter.status().port, config.gateway_port)
            self.assertEqual(adapter.webui_url(), f"http://127.0.0.1:{config.gateway_port + 2}")
            self.assertEqual(
                adapter.build_command(),
                [
                    "node",
                    str(paths.runtime_dir / "openclaw" / "openclaw.mjs"),
                    "gateway",
                    "run",
                    "--port",
                    str(config.gateway_port),
                    "--bind",
                    "loopback",
                    "--allow-unconfigured",
                ],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
