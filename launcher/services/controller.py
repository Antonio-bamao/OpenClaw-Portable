from __future__ import annotations

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.models import LauncherViewState
from launcher.runtime.base import RuntimeAdapter, RuntimeStatus
from launcher.runtime.mock_runtime import MockRuntimeAdapter


class LauncherController:
    def __init__(
        self,
        paths: PortablePaths,
        runtime_adapter: RuntimeAdapter | None = None,
        node_command: str = "node",
    ) -> None:
        self.paths = paths
        self.store = LauncherConfigStore(paths)
        self.runtime_adapter = runtime_adapter or MockRuntimeAdapter(node_command=node_command)
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
        status_detail = runtime_status.message or self._map_status_detail(runtime_status)

        return LauncherViewState(
            status_label=status_label,
            status_detail=status_detail,
            port_label=f"{config.bind_host}:{port}",
            runtime_detail="Node mock runtime / Phase 1 开发版",
            provider_label=f"{config.provider_name} / {config.model}",
            message="当前为开发版 MVP，真实 OpenClaw 运行时将在后续适配层中接入。",
            webui_url=self.runtime_adapter.webui_url(),
            offline_mode=not bool(sensitive.api_key),
        )

    def _prepare_if_needed(self) -> None:
        if self._prepared or self.store.is_first_run():
            return
        config, _ = self.store.load()
        self.runtime_adapter.prepare(config, self.paths)
        self._prepared = True

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
