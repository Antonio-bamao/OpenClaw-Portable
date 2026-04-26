from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path

from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.models import FeishuChannelState, LauncherViewState
from launcher.runtime.base import RuntimeAdapter, RuntimeStatus
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter
from launcher.services.diagnostics_export import DiagnosticsExporter
from launcher.services.factory_reset import FactoryResetService
from launcher.services.feishu_channel import FeishuChannelConfig, FeishuChannelService, FeishuChannelStatus
from launcher.services.local_update import LocalUpdateImportService, RestoreUpdateBackupService
from launcher.services.online_update import OnlineUpdateService, UpdateCheckResult
from launcher.services.provider_bridge import ProviderBridge
from launcher.services.social_channels import (
    OpenClawChannelCommandRunner,
    QqChannelConfig,
    SocialChannelService,
    SocialChannelStatus,
    WechatChannelConfig,
    WecomChannelConfig,
)


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
        self.feishu_channel_service = FeishuChannelService(paths)
        self.social_channel_service = SocialChannelService(paths, OpenClawChannelCommandRunner(paths, node_command=node_command))
        self.provider_bridge = ProviderBridge(paths)
        self._prepared = False

    def configure(self, config: LauncherConfig, sensitive: SensitiveConfig) -> None:
        self.store.save(config, sensitive)
        runtime_config_patch, runtime_env = self._runtime_projection(config, sensitive)
        self._prepare_runtime_adapter(config, runtime_config_patch, runtime_env)
        self._prepared = True
        self._refresh_feishu_runtime_status()

    def start_runtime(self) -> None:
        self._prepare_if_needed()
        self.runtime_adapter.start()
        self._refresh_feishu_runtime_status()

    def stop_runtime(self) -> None:
        self.runtime_adapter.stop()
        self._refresh_feishu_runtime_status()

    def restart_runtime(self) -> None:
        self._prepare_if_needed()
        self.runtime_adapter.restart()
        self._refresh_feishu_runtime_status()

    def should_auto_start_runtime(self) -> bool:
        if self.store.is_first_run() or self.runtime_mode != "openclaw":
            return False
        self._prepare_if_needed()
        runtime_status = self.runtime_adapter.status()
        return runtime_status.state in {"idle", "ready", "stopped"}

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

    def load_feishu_channel_state(self) -> FeishuChannelState:
        if not self.store.is_first_run():
            self._refresh_feishu_runtime_status()
        state = self.feishu_channel_service.build_view_state()
        if self.runtime_mode != "openclaw" and state.enabled and state.status_label == "待启用":
            return replace(
                state,
                status_detail="当前仍在 Node mock runtime。测试连接只校验 App 凭据；切到真实 OpenClaw runtime 并启动后，才能建立飞书私聊链路。",
            )
        return state

    def save_feishu_channel(self, app_id: str, app_secret: str, bot_app_name: str = "OpenClaw Bot") -> FeishuChannelState:
        current = self.feishu_channel_service.load_config()
        config = FeishuChannelConfig(
            app_id=app_id.strip(),
            app_secret=app_secret.strip(),
            enabled=current.enabled,
            bot_app_name=bot_app_name.strip() or "OpenClaw Bot",
            last_validated_at=current.last_validated_at,
        )
        self.feishu_channel_service.save_config(config)
        if not config.app_id or not config.app_secret:
            self.feishu_channel_service.save_status(
                FeishuChannelStatus(state="unconfigured", last_error="", last_connected_at=None, last_message_at=None)
            )
        return self.load_feishu_channel_state()

    def test_feishu_channel(self) -> FeishuChannelState:
        config = self.feishu_channel_service.load_config()
        result = self.feishu_channel_service.validate_credentials(config.app_id, config.app_secret)
        if result.ok:
            self.feishu_channel_service.save_config(replace(config, last_validated_at=result.validated_at))
            self.feishu_channel_service.save_status(FeishuChannelStatus(state=result.state, last_error=""))
        else:
            self.feishu_channel_service.save_status(FeishuChannelStatus(state=result.state, last_error=result.error_message))
        return self.load_feishu_channel_state()

    def enable_feishu_channel(self) -> FeishuChannelState:
        config = self.feishu_channel_service.load_config()
        if not config.app_id.strip() or not config.app_secret.strip():
            self.feishu_channel_service.save_status(
                FeishuChannelStatus(state="invalid_config", last_error="配置无效，请检查 App ID / App Secret。")
            )
            return self.load_feishu_channel_state()
        self.feishu_channel_service.save_config(replace(config, enabled=True))
        self._reproject_feishu_runtime_if_configured()
        return self.load_feishu_channel_state()

    def disable_feishu_channel(self) -> FeishuChannelState:
        config = self.feishu_channel_service.load_config()
        self.feishu_channel_service.save_config(replace(config, enabled=False))
        self.feishu_channel_service.save_status(FeishuChannelStatus(state="pending_enable" if config.app_id and config.app_secret else "unconfigured"))
        self._reproject_feishu_runtime_if_configured()
        return self.load_feishu_channel_state()

    def load_wechat_channel_state(self):
        return self.social_channel_service.build_wechat_view_state()

    def install_wechat_channel(self):
        self.social_channel_service.install_wechat_plugin()
        self._reproject_channels_if_configured()
        return self.load_wechat_channel_state()

    def login_wechat_channel(self):
        self.social_channel_service.open_wechat_login_terminal()
        return self.load_wechat_channel_state()

    def confirm_wechat_channel_login(self):
        self.social_channel_service.confirm_wechat_runtime_login()
        return self.load_wechat_channel_state()

    def enable_wechat_channel(self):
        config = self.social_channel_service.load_wechat_config()
        self.social_channel_service.save_wechat_config(replace(config, enabled=True))
        self.social_channel_service.save_wechat_status(SocialChannelStatus(state="enabled"))
        self._reproject_channels_if_configured()
        return self.load_wechat_channel_state()

    def disable_wechat_channel(self):
        config = self.social_channel_service.load_wechat_config()
        self.social_channel_service.save_wechat_config(replace(config, enabled=False))
        self.social_channel_service.save_wechat_status(SocialChannelStatus(state="pending_enable" if config.installed else "unconfigured"))
        self._reproject_channels_if_configured()
        return self.load_wechat_channel_state()

    def load_qq_channel_state(self):
        return self.social_channel_service.build_qq_view_state()

    def save_qq_channel(self, app_id: str, app_secret: str):
        current = self.social_channel_service.load_qq_config()
        normalized_app_id = app_id.strip()
        normalized_app_secret = app_secret.strip()
        credentials_changed = (
            normalized_app_id != current.app_id.strip() or normalized_app_secret != current.app_secret.strip()
        )
        config = QqChannelConfig(
            app_id=normalized_app_id,
            app_secret=normalized_app_secret,
            enabled=current.enabled and not credentials_changed,
            last_validated_at=current.last_validated_at,
            last_onboarded_token_fingerprint=(
                current.last_onboarded_token_fingerprint if not credentials_changed else None
            ),
        )
        self.social_channel_service.save_qq_config(config)
        if not config.app_id or not config.app_secret:
            self.social_channel_service.save_qq_status(SocialChannelStatus(state="unconfigured"))
        elif credentials_changed:
            self.social_channel_service.save_qq_status(SocialChannelStatus(state="pending_enable"))
        return self.load_qq_channel_state()

    def test_qq_channel(self):
        config = self.social_channel_service.load_qq_config()
        result = self.social_channel_service.validate_qq_config(config)
        if result.ok:
            self.social_channel_service.save_qq_config(replace(config, last_validated_at=result.validated_at))
            self.social_channel_service.save_qq_status(SocialChannelStatus(state=result.state))
        else:
            self.social_channel_service.save_qq_status(SocialChannelStatus(state=result.state, last_error=result.error_message))
        return self.load_qq_channel_state()

    def enable_qq_channel(self):
        config = self.social_channel_service.load_qq_config()
        result = self.social_channel_service.validate_qq_config(config)
        if not result.ok:
            self.social_channel_service.save_qq_status(SocialChannelStatus(state=result.state, last_error=result.error_message))
            return self.load_qq_channel_state()
        onboarding_result = self.social_channel_service.onboard_qq_channel(config)
        if not onboarding_result.ok:
            self.social_channel_service.save_qq_config(replace(config, enabled=False))
            self.social_channel_service.save_qq_status(
                SocialChannelStatus(state="enable_failed", last_error=onboarding_result.error_message or onboarding_result.output)
            )
            return self.load_qq_channel_state()
        config = self.social_channel_service.load_qq_config()
        self.social_channel_service.save_qq_config(replace(config, enabled=True, last_validated_at=result.validated_at))
        self.social_channel_service.save_qq_status(SocialChannelStatus(state="enabled"))
        self._reproject_channels_if_configured()
        return self.load_qq_channel_state()

    def disable_qq_channel(self):
        config = self.social_channel_service.load_qq_config()
        self.social_channel_service.save_qq_config(replace(config, enabled=False))
        self.social_channel_service.save_qq_status(SocialChannelStatus(state="pending_enable" if config.app_id and config.app_secret else "unconfigured"))
        self._reproject_channels_if_configured()
        return self.load_qq_channel_state()

    def load_wecom_channel_state(self):
        return self.social_channel_service.build_wecom_view_state()

    def install_wecom_channel(self):
        self.social_channel_service.install_wecom_plugin()
        return self.load_wecom_channel_state()

    def save_wecom_channel(self, bot_id: str, secret: str):
        current = self.social_channel_service.load_wecom_config()
        config = WecomChannelConfig(
            bot_id=bot_id.strip(),
            secret=secret.strip(),
            enabled=current.enabled,
            connection_mode=current.connection_mode,
            last_validated_at=current.last_validated_at,
        )
        self.social_channel_service.save_wecom_config(config)
        if not config.bot_id or not config.secret:
            self.social_channel_service.save_wecom_status(SocialChannelStatus(state="unconfigured"))
        return self.load_wecom_channel_state()

    def test_wecom_channel(self):
        config = self.social_channel_service.load_wecom_config()
        result = self.social_channel_service.validate_wecom_config(config)
        if result.ok:
            self.social_channel_service.save_wecom_config(replace(config, last_validated_at=result.validated_at))
            self.social_channel_service.save_wecom_status(SocialChannelStatus(state=result.state))
        else:
            self.social_channel_service.save_wecom_status(SocialChannelStatus(state=result.state, last_error=result.error_message))
        return self.load_wecom_channel_state()

    def enable_wecom_channel(self):
        config = self.social_channel_service.load_wecom_config()
        result = self.social_channel_service.validate_wecom_config(config)
        if not result.ok:
            self.social_channel_service.save_wecom_status(SocialChannelStatus(state=result.state, last_error=result.error_message))
            return self.load_wecom_channel_state()
        self.social_channel_service.save_wecom_config(replace(config, enabled=True, last_validated_at=result.validated_at))
        self.social_channel_service.save_wecom_status(SocialChannelStatus(state="enabled"))
        self._reproject_channels_if_configured()
        return self.load_wecom_channel_state()

    def disable_wecom_channel(self):
        config = self.social_channel_service.load_wecom_config()
        self.social_channel_service.save_wecom_config(replace(config, enabled=False))
        self.social_channel_service.save_wecom_status(SocialChannelStatus(state="pending_enable" if config.bot_id and config.secret else "unconfigured"))
        self._reproject_channels_if_configured()
        return self.load_wecom_channel_state()

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
        self._refresh_feishu_runtime_status()
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
        self._refresh_feishu_runtime_status()
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
        config, sensitive = self.store.load()
        runtime_config_patch, runtime_env = self._runtime_projection(config, sensitive)
        self._prepare_runtime_adapter(config, runtime_config_patch, runtime_env)
        self._prepared = True

    def _runtime_projection(
        self,
        config: LauncherConfig,
        sensitive: SensitiveConfig,
    ) -> tuple[dict[str, object], dict[str, str]]:
        provider_projection = self.provider_bridge.apply(config, sensitive)
        channel_config_patch, runtime_env = self._channel_runtime_projection()
        runtime_config_patch = self._deep_merge(provider_projection.runtime_config_patch, channel_config_patch)
        return runtime_config_patch, runtime_env

    def _channel_runtime_projection(self) -> tuple[dict[str, object], dict[str, str]]:
        feishu_config_patch, feishu_env = self._feishu_runtime_projection()
        social_config_patch, social_env = self._social_runtime_projection()
        return self._deep_merge(feishu_config_patch, social_config_patch), {**feishu_env, **social_env}

    def _feishu_runtime_projection(self) -> tuple[dict[str, object], dict[str, str]]:
        feishu_config = self.feishu_channel_service.load_config()
        if not (feishu_config.app_id.strip() or feishu_config.app_secret.strip() or feishu_config.enabled):
            return {}, {}
        projection = self.feishu_channel_service.build_runtime_projection(feishu_config)
        if not feishu_config.app_id.strip() or not feishu_config.app_secret.strip():
            return projection.runtime_config_patch, {}
        return projection.runtime_config_patch, projection.runtime_env

    def _social_runtime_projection(self) -> tuple[dict[str, object], dict[str, str]]:
        runtime_config_patch: dict[str, object] = {}
        runtime_env: dict[str, str] = {}

        wechat_config = self.social_channel_service.load_wechat_config()
        if wechat_config.enabled or wechat_config.installed:
            projection = self.social_channel_service.build_wechat_runtime_projection(wechat_config)
            runtime_config_patch = self._deep_merge(runtime_config_patch, projection.runtime_config_patch)
            runtime_env.update(projection.runtime_env)

        qq_config = self.social_channel_service.load_qq_config()
        if qq_config.enabled or qq_config.app_id.strip() or qq_config.app_secret.strip():
            projection = self.social_channel_service.build_qq_runtime_projection(qq_config)
            runtime_config_patch = self._deep_merge(runtime_config_patch, projection.runtime_config_patch)
            runtime_env.update(projection.runtime_env)

        wecom_config = self.social_channel_service.load_wecom_config()
        if wecom_config.enabled or wecom_config.bot_id.strip() or wecom_config.secret.strip():
            projection = self.social_channel_service.build_wecom_runtime_projection(wecom_config)
            runtime_config_patch = self._deep_merge(runtime_config_patch, projection.runtime_config_patch)
            runtime_env.update(projection.runtime_env)

        return runtime_config_patch, runtime_env

    def _prepare_runtime_adapter(
        self,
        config: LauncherConfig,
        runtime_config_patch: dict[str, object],
        runtime_env: dict[str, str],
    ) -> None:
        prepare_signature = inspect.signature(self.runtime_adapter.prepare)
        supports_projection = (
            "runtime_config_patch" in prepare_signature.parameters
            or "runtime_env" in prepare_signature.parameters
            or any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in prepare_signature.parameters.values())
        )
        if supports_projection:
            self.runtime_adapter.prepare(
                config,
                self.paths,
                runtime_config_patch=runtime_config_patch,
                runtime_env=runtime_env,
            )
            return
        self.runtime_adapter.prepare(config, self.paths)

    def _refresh_feishu_runtime_status(self) -> None:
        runtime_status = self.runtime_adapter.status()
        self.feishu_channel_service.refresh_runtime_status(
            runtime_status.state,
            runtime_status.message or "",
            runtime_link_available=self.runtime_mode == "openclaw",
        )

    def _reproject_feishu_runtime_if_configured(self) -> None:
        self._reproject_channels_if_configured()

    def _reproject_channels_if_configured(self) -> None:
        if self.store.is_first_run():
            return
        config, sensitive = self.store.load()
        runtime_config_patch, runtime_env = self._runtime_projection(config, sensitive)
        self._prepare_runtime_adapter(config, runtime_config_patch, runtime_env)
        self._prepared = True

    def _deep_merge(self, base: dict[str, object], patch: dict[str, object]) -> dict[str, object]:
        merged: dict[str, object] = dict(base)
        for key, value in patch.items():
            existing_value = merged.get(key)
            if isinstance(value, dict) and isinstance(existing_value, dict):
                merged[key] = self._deep_merge(existing_value, value)
                continue
            merged[key] = value
        return merged

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
        version_info = json.loads(version_file.read_text(encoding="utf-8"))
        version = str(version_info.get("version") or "").strip()
        if not version:
            raise ValueError("当前便携包缺少有效版本号，无法检查更新。")
        return version
