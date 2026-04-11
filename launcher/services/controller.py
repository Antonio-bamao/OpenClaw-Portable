from __future__ import annotations

from pathlib import Path

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.models import LauncherViewState
from launcher.runtime.base import RuntimeAdapter, RuntimeStatus
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter
from launcher.services.diagnostics_export import DiagnosticsExporter
from launcher.services.factory_reset import FactoryResetService
from launcher.services.local_update import LocalUpdateImportService, RestoreUpdateBackupService
from launcher.services.online_update import OnlineUpdateService, UpdateCheckResult


class LauncherController:
    def __init__(
        self,
        paths: PortablePaths,
        runtime_adapter: RuntimeAdapter | None = None,
        diagnostics_exporter: DiagnosticsExporter | None = None,
        factory_reset_service: FactoryResetService | None = None,
        local_update_service: LocalUpdateImportService | None = None,
        restore_update_backup_service: RestoreUpdateBackupService | None = None,
        online_update_service: OnlineUpdateService | None = None,
        runtime_mode: str = "mock",
        node_command: str = "node",
    ) -> None:
        self.paths = paths
        self.store = LauncherConfigStore(paths)
        self.runtime_mode = runtime_mode
        self.runtime_adapter = runtime_adapter or self._build_runtime_adapter(runtime_mode, node_command)
        self.diagnostics_exporter = diagnostics_exporter or DiagnosticsExporter(
            paths,
            store=self.store,
            runtime_mode=runtime_mode,
        )
        self.factory_reset_service = factory_reset_service or FactoryResetService(paths)
        self.local_update_service = local_update_service or LocalUpdateImportService(paths)
        self.restore_update_backup_service = restore_update_backup_service or RestoreUpdateBackupService(paths)
        self.online_update_service = online_update_service or OnlineUpdateService(paths)
        self._prepared = False

    def configure(self, config: LauncherConfig, sensitive: SensitiveConfig) -> None:
        self.store.save(config, sensitive)
        self.runtime_adapter.prepare(config, self.paths)
        self._prepared = True

    def start_runtime(self) -> None:
        self._prepare_if_needed()
        self.runtime_adapter.start()

    def stop_runtime(self) -> None:
        self.runtime_adapter.stop()

    def restart_runtime(self) -> None:
        self._prepare_if_needed()
        self.runtime_adapter.restart()

    def export_diagnostics_bundle(self) -> Path:
        return self.diagnostics_exporter.export_bundle()

    def reset_factory_state(self) -> bool:
        self.runtime_adapter.stop()
        self.factory_reset_service.reset()
        self._prepared = False
        return True

    def import_update_package(self, package_root: Path) -> str:
        self.runtime_adapter.stop()
        result = self.local_update_service.import_package(package_root)
        self._prepared = False
        return result.imported_version

    def restore_update_backup(self, backup_root: Path) -> str:
        self.runtime_adapter.stop()
        result = self.restore_update_backup_service.restore_backup(backup_root)
        self._prepared = False
        return result.restored_version

    def check_for_updates(self) -> UpdateCheckResult:
        return self.online_update_service.check_for_updates(self._current_package_version())

    def download_and_import_update(self, metadata: UpdateCheckResult) -> str:
        self.runtime_adapter.stop()
        package_root = self.online_update_service.download_update_package(metadata)
        result = self.local_update_service.import_package(package_root)
        self._prepared = False
        return result.imported_version

    def load_view_state(self) -> LauncherViewState:
        if self.store.is_first_run():
            return LauncherViewState(
                status_label="未配置",
                status_detail="还没有完成首次引导配置。",
                port_label="待配置",
                runtime_detail="尚未准备运行时",
                provider_label="未配置 Provider",
                message="先完成首次向导，再进入主控制台。",
                webui_url="",
                offline_mode=True,
            )

        config, sensitive = self.store.load()
        self._prepare_if_needed()
        runtime_status = self.runtime_adapter.status()
        status_label = self._map_status_label(runtime_status)
        port = runtime_status.port or config.gateway_port
        status_detail = self._build_status_detail(runtime_status)

        return LauncherViewState(
            status_label=status_label,
            status_detail=status_detail,
            port_label=f"{config.bind_host}:{port}",
            runtime_detail=self._runtime_detail(),
            provider_label=self._provider_label(config),
            message=self._runtime_message(config, sensitive),
            webui_url=self.runtime_adapter.webui_url(),
            offline_mode=not bool(sensitive.api_key),
        )

    def load_pending_runtime_view_state(self, action: str = "start") -> LauncherViewState:
        if self.store.is_first_run():
            return self.load_view_state()

        config, sensitive = self.store.load()
        self._prepare_if_needed()
        runtime_status = self.runtime_adapter.status()
        port = runtime_status.port or config.gateway_port

        return LauncherViewState(
            status_label="重启中" if action == "restart" else "启动中",
            status_detail=self._pending_status_detail(action),
            port_label=f"{config.bind_host}:{port}",
            runtime_detail=self._runtime_detail(),
            provider_label=self._provider_label(config),
            message=self._pending_runtime_message(config, sensitive, action),
            webui_url="",
            offline_mode=not bool(sensitive.api_key),
        )

    def _prepare_if_needed(self) -> None:
        if self._prepared or self.store.is_first_run():
            return
        config, _ = self.store.load()
        self.runtime_adapter.prepare(config, self.paths)
        self._prepared = True

    def _build_runtime_adapter(self, runtime_mode: str, node_command: str) -> RuntimeAdapter:
        if runtime_mode == "mock":
            return MockRuntimeAdapter(node_command=node_command)
        if runtime_mode == "openclaw":
            return OpenClawRuntimeAdapter(node_command=node_command)
        raise ValueError(f"Unsupported runtime_mode: {runtime_mode}")

    def _runtime_detail(self) -> str:
        if self.runtime_mode == "openclaw":
            return "OpenClaw gateway / v2026.4.8"
        return "Node mock runtime / Phase 1 开发版"

    def _runtime_message(self, config: LauncherConfig, sensitive: SensitiveConfig) -> str:
        provider_issue = self._provider_configuration_issue(config)
        if provider_issue:
            return provider_issue
        if not sensitive.api_key:
            return f"{config.provider_name} 的 API Key 尚未配置。可以先预览本地控制台；需要真实对话时请点击“重新配置”补充 Key。"
        if self.runtime_mode == "openclaw":
            return "当前正在使用真实 OpenClaw gateway，本地控制台由便携运行时提供。"
        return "当前为开发版 MVP，真实 OpenClaw 运行时将在后续适配层中接入。"

    def _pending_runtime_message(self, config: LauncherConfig, sensitive: SensitiveConfig, action: str) -> str:
        provider_issue = self._provider_configuration_issue(config)
        if provider_issue:
            return f"{provider_issue} 建议先点击“重新配置”补全后再启动。"
        if self.runtime_mode == "openclaw":
            message = (
                "正在重新启动真实 OpenClaw gateway，请勿关闭窗口。"
                if action == "restart"
                else "正在启动真实 OpenClaw gateway，首次启动可能需要 20-90 秒，请勿关闭窗口。"
            )
            if not sensitive.api_key:
                return f"{message} 当前未配置 {config.provider_name} 的 API Key，启动后仍需通过“重新配置”补充。"
            return message
        return "正在启动本地 mock runtime，请稍候。"

    def _map_status_label(self, runtime_status: RuntimeStatus) -> str:
        mapping = {
            "running": "运行中",
            "stopped": "已停止",
            "ready": "已就绪",
            "idle": "未启动",
        }
        return mapping.get(runtime_status.state, "状态未知")

    def _map_status_detail(self, runtime_status: RuntimeStatus) -> str:
        mapping = {
            "running": "本地运行时正在响应请求。",
            "stopped": "服务已停止，可随时重新启动。",
            "ready": "配置已加载，等待启动服务。",
            "idle": "请先完成配置。",
        }
        return mapping.get(runtime_status.state, "服务状态暂不可用。")

    def _pending_status_detail(self, action: str) -> str:
        if self.runtime_mode == "openclaw":
            if action == "restart":
                return "正在重新连接本地 gateway，请稍等。"
            return "正在等待本地 gateway 就绪，首次启动可能需要 20-90 秒。"
        return "正在启动本地 mock runtime，通常会在几秒内完成。"

    def _provider_label(self, config: LauncherConfig) -> str:
        model_label = config.model or "待补充模型"
        return f"{config.provider_name} / {model_label}"

    def _provider_configuration_issue(self, config: LauncherConfig) -> str | None:
        missing_fields: list[str] = []
        if not config.base_url.strip():
            missing_fields.append("接口地址")
        if not config.model.strip():
            missing_fields.append("模型名")
        if not missing_fields:
            return None
        missing_summary = "和".join(missing_fields)
        return f"{config.provider_name} Provider 还没配置完整，缺少{missing_summary}。请点击“重新配置”补全。"

    def _build_status_detail(self, runtime_status: RuntimeStatus) -> str:
        duration_label = self._runtime_duration_label(runtime_status.uptime_seconds)
        if runtime_status.state == "running" and duration_label:
            if runtime_status.message:
                return f"{runtime_status.message} 当前会话已运行 {duration_label}。"
            return f"本地运行时正在响应请求，已运行 {duration_label}。"
        return runtime_status.message or self._map_status_detail(runtime_status)

    def _runtime_duration_label(self, uptime_seconds: int | None) -> str | None:
        if uptime_seconds is None:
            return None
        minutes, seconds = divmod(uptime_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _current_package_version(self) -> str:
        version_file = self.paths.project_root / "version.json"
        if not version_file.exists():
            raise FileNotFoundError("当前便携包缺少 version.json，无法检查更新。")
        import json

        version_info = json.loads(version_file.read_text(encoding="utf-8"))
        version = str(version_info.get("version") or "").strip()
        if not version:
            raise ValueError("当前便携包缺少有效版本号，无法检查更新。")
        return version
