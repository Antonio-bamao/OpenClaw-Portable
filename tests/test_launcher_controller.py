import shutil
import socket
import time
import unittest
import uuid
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.base import RuntimeHealth, RuntimeStatus
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter
from launcher.services.controller import LauncherController
from launcher.services.feishu_channel import FeishuChannelConfig
from launcher.services.social_channels import QqChannelConfig, WechatChannelConfig, WecomChannelConfig


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


@dataclass
class FakeRestoreResult:
    restored_version: str


class FakeRuntimeAdapter:
    def __init__(self, runtime_state: str = "ready", runtime_message: str = "ready") -> None:
        self.stop_calls = 0
        self.runtime_state = runtime_state
        self.runtime_message = runtime_message
        self.last_runtime_config_patch: dict[str, object] = {}
        self.last_runtime_env: dict[str, str] = {}

    def prepare(
        self,
        config: LauncherConfig,
        paths: PortablePaths,
        runtime_config_patch: dict[str, object] | None = None,
        runtime_env: dict[str, str] | None = None,
    ) -> None:
        self.last_runtime_config_patch = runtime_config_patch or {}
        self.last_runtime_env = runtime_env or {}

    def start(self) -> None:
        return None

    def stop(self) -> None:
        self.stop_calls += 1

    def restart(self) -> None:
        return None

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(state=self.runtime_state, port=18789, message=self.runtime_message)

    def webui_url(self) -> str:
        return "http://127.0.0.1:18789"

    def healthcheck(self) -> RuntimeHealth:
        return RuntimeHealth(ok=True)


class FakeRestoreUpdateBackupService:
    def __init__(self, restored_version: str = "v1") -> None:
        self.restored_version = restored_version
        self.called_with: Path | None = None

    def restore_backup(self, backup_root: Path) -> FakeRestoreResult:
        self.called_with = backup_root
        return FakeRestoreResult(restored_version=self.restored_version)


@dataclass
class FakeUpdateCheckResult:
    update_available: bool
    latest_version: str
    notes: list[str]
    package_url: str


class FakeOnlineUpdateService:
    def __init__(self, *, check_result: FakeUpdateCheckResult, package_dir: Path | None = None) -> None:
        self.check_result = check_result
        self.package_dir = package_dir
        self.check_called_with: str | None = None
        self.download_called_with: FakeUpdateCheckResult | None = None

    def check_for_updates(self, current_version: str) -> FakeUpdateCheckResult:
        self.check_called_with = current_version
        return self.check_result

    def download_update_package(self, metadata: FakeUpdateCheckResult) -> Path:
        self.download_called_with = metadata
        if self.package_dir is None:
            raise AssertionError("package_dir not configured")
        return self.package_dir


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

    def test_restore_update_backup_stops_runtime_and_resets_prepared_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            restore_service = FakeRestoreUpdateBackupService(restored_version="v2026.04.01")
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                restore_update_backup_service=restore_service,
                node_command="node",
            )
            controller.configure(make_config(reserve_free_port()), SensitiveConfig(api_key="sk-demo"))

            restored_version = controller.restore_update_backup(Path("C:/tmp/update-backup"))

            self.assertEqual(restored_version, "v2026.04.01")
            self.assertEqual(runtime_adapter.stop_calls, 1)
            self.assertEqual(restore_service.called_with, Path("C:/tmp/update-backup"))
            self.assertFalse(controller._prepared)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_check_for_updates_uses_current_version_file(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            (paths.project_root / "version.json").write_text('{"version": "v2026.04.1"}', encoding="utf-8")
            online_update_service = FakeOnlineUpdateService(
                check_result=FakeUpdateCheckResult(
                    update_available=True,
                    latest_version="v2026.04.2",
                    notes=["upgrade"],
                    package_url="https://example.com/pkg.zip",
                )
            )
            controller = LauncherController(paths, online_update_service=online_update_service, node_command="node")

            result = controller.check_for_updates()

            self.assertTrue(result.update_available)
            self.assertEqual(online_update_service.check_called_with, "v2026.04.1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_download_and_import_update_stops_runtime_and_resets_prepared_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            package_dir = Path("C:/tmp/downloaded-package")
            online_update_service = FakeOnlineUpdateService(
                check_result=FakeUpdateCheckResult(
                    update_available=True,
                    latest_version="v2026.04.2",
                    notes=["upgrade"],
                    package_url="https://example.com/pkg.zip",
                ),
                package_dir=package_dir,
            )
            local_update_service = type(
                "FakeLocalUpdateService",
                (),
                {
                    "__init__": lambda self: None,
                    "called_with": None,
                    "import_package": lambda self, root: type("Result", (), {"imported_version": "v2026.04.2"})(),
                },
            )()
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                local_update_service=local_update_service,
                online_update_service=online_update_service,
                node_command="node",
            )
            controller._prepared = True
            metadata = online_update_service.check_result

            imported_version = controller.download_and_import_update(metadata)

            self.assertEqual(imported_version, "v2026.04.2")
            self.assertEqual(runtime_adapter.stop_calls, 1)
            self.assertEqual(online_update_service.download_called_with, metadata)
            self.assertFalse(controller._prepared)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_controller_passes_feishu_projection_into_runtime_prepare(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )
            controller.feishu_channel_service.save_config(
                FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True)
            )

            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            self.assertEqual(runtime_adapter.last_runtime_env["FEISHU_APP_ID"], "cli_xxx")
            self.assertEqual(runtime_adapter.last_runtime_env["FEISHU_APP_SECRET"], "secret")
            self.assertTrue(runtime_adapter.last_runtime_config_patch["channels"]["feishu"]["enabled"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_controller_passes_wechat_qq_and_wecom_projection_into_runtime_prepare(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )
            controller.social_channel_service.save_wechat_config(WechatChannelConfig(enabled=True, installed=True))
            controller.social_channel_service.save_qq_config(QqChannelConfig(app_id="123456", app_secret="secret", enabled=True))
            controller.social_channel_service.save_wecom_config(WecomChannelConfig(bot_id="wwbot", secret="wecom-secret", enabled=True))

            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            patch = runtime_adapter.last_runtime_config_patch
            self.assertTrue(patch["plugins"]["entries"]["openclaw-weixin"]["enabled"])
            self.assertTrue(patch["channels"]["openclaw-weixin"]["enabled"])
            self.assertEqual(patch["channels"]["qqbot"]["appId"], "123456")
            self.assertEqual(patch["channels"]["qqbot"]["clientSecret"], "secret")
            self.assertEqual(patch["channels"]["wecom"]["botId"], "wwbot")
            self.assertEqual(patch["channels"]["wecom"]["secret"], "wecom-secret")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_controller_saves_and_enables_qq_and_wecom_channels(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )
            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            saved_qq = controller.save_qq_channel(" 123456 ", " qq-secret ")
            enabled_qq = controller.enable_qq_channel()
            saved_wecom = controller.save_wecom_channel(" wwbot ", " wecom-secret ")
            enabled_wecom = controller.enable_wecom_channel()

            self.assertEqual(saved_qq.app_id, "123456")
            self.assertTrue(enabled_qq.enabled)
            self.assertEqual(saved_wecom.bot_id, "wwbot")
            self.assertTrue(enabled_wecom.enabled)
            self.assertEqual(runtime_adapter.last_runtime_config_patch["channels"]["qqbot"]["clientSecret"], "qq-secret")
            self.assertEqual(runtime_adapter.last_runtime_config_patch["channels"]["wecom"]["secret"], "wecom-secret")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_controller_skips_feishu_projection_when_channel_config_is_invalid(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            paths.feishu_channel_config_file.write_text("{not-json", encoding="utf-8")
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )

            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

            self.assertEqual(runtime_adapter.last_runtime_config_patch, {})
            self.assertEqual(runtime_adapter.last_runtime_env, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_controller_refreshes_feishu_status_when_runtime_is_running(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter(runtime_state="running", runtime_message="feishu ready")
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )
            controller.feishu_channel_service.save_config(
                FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True)
            )

            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))
            controller.load_view_state()

            self.assertEqual(controller.feishu_channel_service.load_status().state, "connected")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("launcher.services.feishu_channel.urlopen")
    def test_controller_saves_tests_and_enables_feishu_channel(self, mock_urlopen) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter(runtime_state="ready", runtime_message="ready")
            controller = LauncherController(
                paths,
                runtime_adapter=runtime_adapter,
                runtime_mode="openclaw",
                node_command="node",
            )
            controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.read.return_value = b'{"code":0,"tenant_access_token":"t-123"}'

            saved_state = controller.save_feishu_channel(" cli_xxx ", " secret ", "Support Bot")
            tested_state = controller.test_feishu_channel()
            enabled_state = controller.enable_feishu_channel()

            self.assertEqual(saved_state.app_id, "cli_xxx")
            self.assertEqual(tested_state.status_label, "待启用")
            self.assertTrue(enabled_state.enabled)
            self.assertEqual(enabled_state.status_label, "连接中")
            self.assertEqual(runtime_adapter.last_runtime_env["FEISHU_APP_ID"], "cli_xxx")
            self.assertTrue(runtime_adapter.last_runtime_config_patch["channels"]["feishu"]["enabled"])
            self.assertEqual(runtime_adapter.last_runtime_config_patch["channels"]["feishu"]["botAppName"], "Support Bot")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
