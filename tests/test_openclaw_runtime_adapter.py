import json
import os
import shutil
import socket
import subprocess
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.base import RuntimeHealth
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

    def test_wait_until_ready_returns_after_first_healthy_gateway_check(self) -> None:
        adapter = OpenClawRuntimeAdapter(startup_timeout_seconds=1, health_poll_interval_seconds=0)
        health_results = [
            RuntimeHealth(ok=True),
            RuntimeHealth(ok=False, error="should not be reached"),
        ]
        observed: list[RuntimeHealth] = []

        def next_healthcheck() -> RuntimeHealth:
            health = health_results.pop(0)
            observed.append(health)
            return health

        adapter.healthcheck = next_healthcheck  # type: ignore[method-assign]

        adapter._wait_until_ready()

        self.assertEqual([health.ok for health in observed], [True])

    def test_wait_until_ready_raises_when_process_exits_before_gateway_is_reachable(self) -> None:
        adapter = OpenClawRuntimeAdapter(startup_timeout_seconds=1, health_poll_interval_seconds=0)
        adapter._process = type("FakeProcess", (), {"poll": lambda self: 23})()
        adapter.healthcheck = lambda: RuntimeHealth(ok=False, error="connection refused")  # type: ignore[method-assign]

        with self.assertRaisesRegex(RuntimeError, "exited before becoming healthy"):
            adapter._wait_until_ready()

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
            self.assertEqual(environment["OPENCLAW_CONFIG_PATH"], str(paths.runtime_config_file))
            self.assertEqual(environment["OPENCLAW_LOG_DIR"], str(paths.logs_dir))
            self.assertEqual(environment["OPENCLAW_CACHE_DIR"], str(paths.cache_dir))
            self.assertEqual(environment["OPENCLAW_API_KEY"], "sk-demo")
            self.assertEqual(environment.get("PATH"), os.environ.get("PATH"))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("launcher.runtime.openclaw_runtime.subprocess.Popen")
    def test_start_hides_windows_console_for_openclaw_gateway_process(self, mock_popen) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            paths.ensure_directories()
            runtime_dir = paths.runtime_dir / "openclaw"
            runtime_dir.mkdir(parents=True, exist_ok=True)
            (runtime_dir / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (runtime_dir / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")

            fake_process = mock_popen.return_value
            fake_process.poll.return_value = None

            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(reserve_free_port()), paths)

            with patch.object(adapter, "_wait_until_ready", return_value=None):
                adapter.start()

            creationflags = mock_popen.call_args.kwargs.get("creationflags", 0)
            self.assertEqual(creationflags, getattr(subprocess, "CREATE_NO_WINDOW", 0))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_environment_merges_runtime_environment_projection(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            config = make_config(reserve_free_port())
            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(
                config,
                paths,
                runtime_env={
                    "FEISHU_APP_ID": "cli_xxx",
                    "FEISHU_APP_SECRET": "secret",
                },
            )

            environment = adapter.build_environment()

            self.assertEqual(environment["FEISHU_APP_ID"], "cli_xxx")
            self.assertEqual(environment["FEISHU_APP_SECRET"], "secret")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prepare_merges_runtime_config_patch_into_openclaw_config(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            paths.ensure_directories()
            paths.runtime_config_file.write_text(
                '{"provider_id":"dashscope","channels":{"slack":{"enabled":true}}}',
                encoding="utf-8",
            )
            config = make_config(reserve_free_port())
            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(
                config,
                paths,
                runtime_config_patch={
                    "channels": {
                        "feishu": {
                            "enabled": True,
                        }
                    }
                },
            )

            merged = json.loads(paths.runtime_config_file.read_text(encoding="utf-8"))

            self.assertEqual(merged["provider_id"], "dashscope")
            self.assertTrue(merged["channels"]["slack"]["enabled"])
            self.assertTrue(merged["channels"]["feishu"]["enabled"])
            self.assertNotIn("botAppName", merged["channels"]["feishu"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_webui_url_uses_gateway_port_and_default_token_after_prepare(self) -> None:
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
            self.assertEqual(adapter.webui_url(), f"http://127.0.0.1:{config.gateway_port}/#token=uclaw")
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

    def test_webui_url_uses_runtime_auth_token_when_available(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            paths.ensure_directories()
            paths.runtime_config_file.write_text(
                '{"gateway":{"auth":{"mode":"token","token":"demo-runtime-token"}}}',
                encoding="utf-8",
            )
            adapter = OpenClawRuntimeAdapter()
            config = make_config(reserve_free_port())
            entrypoint = paths.runtime_dir / "openclaw" / "openclaw.mjs"
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text("#!/usr/bin/env node\n", encoding="utf-8")

            adapter.prepare(config, paths)

            self.assertEqual(adapter.webui_url(), f"http://127.0.0.1:{config.gateway_port}/#token=demo-runtime-token")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_can_stage_openclaw_runtime_to_local_cache_before_starting(self) -> None:
        temp_dir = make_workspace_temp_dir()
        previous_override = os.environ.get("OPENCLAW_PORTABLE_STAGE_RUNTIME")
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            source_runtime = paths.runtime_dir / "openclaw"
            source_runtime.mkdir(parents=True, exist_ok=True)
            (source_runtime / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")
            (source_runtime / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (source_runtime / "dist").mkdir()
            (source_runtime / "dist" / "entry.js").write_text("export {};\n", encoding="utf-8")
            os.environ["OPENCLAW_PORTABLE_STAGE_RUNTIME"] = "1"
            adapter = OpenClawRuntimeAdapter()

            adapter.prepare(make_config(reserve_free_port()), paths)

            command = adapter.build_command()
            cached_entrypoint = Path(command[1])
            self.assertNotEqual(cached_entrypoint, source_runtime / "openclaw.mjs")
            self.assertTrue(cached_entrypoint.is_relative_to(paths.cache_dir))
            self.assertEqual(cached_entrypoint.name, "openclaw.mjs")
            self.assertTrue((cached_entrypoint.parent / "dist" / "entry.js").exists())
            self.assertTrue((source_runtime / "dist" / "entry.js").exists())
        finally:
            if previous_override is None:
                os.environ.pop("OPENCLAW_PORTABLE_STAGE_RUNTIME", None)
            else:
                os.environ["OPENCLAW_PORTABLE_STAGE_RUNTIME"] = previous_override
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prepare_bridges_feishu_extension_runtime_dependency_into_root_node_modules(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            source_runtime = paths.runtime_dir / "openclaw"
            feishu_sdk = (
                source_runtime
                / "dist"
                / "extensions"
                / "feishu"
                / "node_modules"
                / "@larksuiteoapi"
                / "node-sdk"
            )
            feishu_sdk.mkdir(parents=True, exist_ok=True)
            (source_runtime / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")
            (source_runtime / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (feishu_sdk / "package.json").write_text('{"name":"@larksuiteoapi/node-sdk","version":"1.60.0"}', encoding="utf-8")

            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(reserve_free_port()), paths)

            bridged_sdk = source_runtime / "node_modules" / "@larksuiteoapi" / "node-sdk" / "package.json"
            self.assertTrue(bridged_sdk.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prepare_bridges_transitive_feishu_runtime_dependencies_into_root_node_modules(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            source_runtime = paths.runtime_dir / "openclaw"
            feishu_root = source_runtime / "dist" / "extensions" / "feishu" / "node_modules"
            feishu_sdk = feishu_root / "@larksuiteoapi" / "node-sdk"
            axios_dir = feishu_root / "axios"
            redirects_dir = feishu_root / "follow-redirects"

            feishu_sdk.mkdir(parents=True, exist_ok=True)
            axios_dir.mkdir(parents=True, exist_ok=True)
            redirects_dir.mkdir(parents=True, exist_ok=True)

            (source_runtime / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")
            (source_runtime / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (feishu_sdk / "package.json").write_text(
                '{"name":"@larksuiteoapi/node-sdk","version":"1.60.0","dependencies":{"axios":"^1.13.6"}}',
                encoding="utf-8",
            )
            (axios_dir / "package.json").write_text(
                '{"name":"axios","version":"1.13.6","dependencies":{"follow-redirects":"^1.15.11"}}',
                encoding="utf-8",
            )
            (redirects_dir / "package.json").write_text(
                '{"name":"follow-redirects","version":"1.15.11"}',
                encoding="utf-8",
            )

            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(reserve_free_port()), paths)

            self.assertTrue((source_runtime / "node_modules" / "@larksuiteoapi" / "node-sdk" / "package.json").exists())
            self.assertTrue((source_runtime / "node_modules" / "axios" / "package.json").exists())
            self.assertTrue((source_runtime / "node_modules" / "follow-redirects" / "package.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prepare_bridges_discord_extension_runtime_dependencies_into_root_node_modules(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            source_runtime = paths.runtime_dir / "openclaw"
            discord_root = source_runtime / "dist" / "extensions" / "discord" / "node_modules"
            carbon_dir = discord_root / "@buape" / "carbon"
            api_types_dir = discord_root / "discord-api-types"

            carbon_dir.mkdir(parents=True, exist_ok=True)
            api_types_dir.mkdir(parents=True, exist_ok=True)

            (source_runtime / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")
            (source_runtime / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (carbon_dir / "package.json").write_text(
                '{"name":"@buape/carbon","version":"0.14.0","dependencies":{"discord-api-types":"0.38.37"}}',
                encoding="utf-8",
            )
            (api_types_dir / "package.json").write_text(
                '{"name":"discord-api-types","version":"0.38.37"}',
                encoding="utf-8",
            )

            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(reserve_free_port()), paths)

            self.assertTrue((source_runtime / "node_modules" / "@buape" / "carbon" / "package.json").exists())
            self.assertTrue((source_runtime / "node_modules" / "discord-api-types" / "package.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prepare_bridges_slack_extension_runtime_dependencies_into_root_node_modules(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            source_runtime = paths.runtime_dir / "openclaw"
            slack_root = source_runtime / "dist" / "extensions" / "slack" / "node_modules"
            web_api_dir = slack_root / "@slack" / "web-api"
            logger_dir = slack_root / "@slack" / "logger"

            web_api_dir.mkdir(parents=True, exist_ok=True)
            logger_dir.mkdir(parents=True, exist_ok=True)

            (source_runtime / "openclaw.mjs").write_text("#!/usr/bin/env node\n", encoding="utf-8")
            (source_runtime / "package.json").write_text('{"name":"openclaw","version":"test"}', encoding="utf-8")
            (web_api_dir / "package.json").write_text(
                '{"name":"@slack/web-api","version":"7.15.0","dependencies":{"@slack/logger":"^4.0.1"}}',
                encoding="utf-8",
            )
            (logger_dir / "package.json").write_text(
                '{"name":"@slack/logger","version":"4.0.1"}',
                encoding="utf-8",
            )

            adapter = OpenClawRuntimeAdapter()
            adapter.prepare(make_config(reserve_free_port()), paths)

            self.assertTrue((source_runtime / "node_modules" / "@slack" / "web-api" / "package.json").exists())
            self.assertTrue((source_runtime / "node_modules" / "@slack" / "logger" / "package.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
