from __future__ import annotations

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.models import LauncherViewState
from launcher.runtime.base import RuntimeAdapter, RuntimeStatus
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter


class LauncherController:
    def __init__(
        self,
        paths: PortablePaths,
        runtime_adapter: RuntimeAdapter | None = None,
        runtime_mode: str = "mock",
        node_command: str = "node",
    ) -> None:
        self.paths = paths
        self.store = LauncherConfigStore(paths)
        self.runtime_mode = runtime_mode
        self.runtime_adapter = runtime_adapter or self._build_runtime_adapter(runtime_mode, node_command)
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
            provider_label=f"{config.provider_name} / {config.model}",
            message=self._runtime_message(config, sensitive),
            webui_url=self.runtime_adapter.webui_url(),
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
        if not sensitive.api_key:
            return f"{config.provider_name} 的 API Key 尚未配置。可以先预览本地控制台；需要真实对话时请点击“重新配置”补充 Key。"
        if self.runtime_mode == "openclaw":
            return "当前正在使用真实 OpenClaw gateway，本地控制台由便携运行时提供。"
        return "当前为开发版 MVP，真实 OpenClaw 运行时将在后续适配层中接入。"

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
