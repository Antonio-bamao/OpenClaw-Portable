from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from launcher.core.config_store import LauncherConfigStore
from launcher.core.paths import PortablePaths
from launcher.services.feishu_channel import FeishuChannelService
from launcher.services.social_channels import SocialChannelService


class DiagnosticsExporter:
    def __init__(
        self,
        paths: PortablePaths,
        *,
        store: LauncherConfigStore | None = None,
        runtime_mode: str = "mock",
    ) -> None:
        self.paths = paths
        self.store = store or LauncherConfigStore(paths)
        self.runtime_mode = runtime_mode

    def export_bundle(self) -> Path:
        self.paths.ensure_directories()
        export_dir = self.paths.state_dir / "backups"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bundle_path = export_dir / f"openclaw-diagnostics-{timestamp}.zip"
        logs = sorted(path for path in self.paths.logs_dir.glob("*.log") if path.is_file())

        with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "createdAt": datetime.now().isoformat(timespec="seconds"),
                        "runtimeMode": self.runtime_mode,
                        "logsIncluded": [path.name for path in logs],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            archive.writestr(
                "config-summary.json",
                json.dumps(self._config_summary(), ensure_ascii=False, indent=2),
            )
            version_file = self.paths.project_root / "version.json"
            if version_file.exists():
                archive.writestr("version.json", version_file.read_text(encoding="utf-8"))
            for log_file in logs:
                archive.write(log_file, arcname=f"logs/{log_file.name}")
        return bundle_path

    def _config_summary(self) -> dict[str, object]:
        if self.store.is_first_run():
            return {
                "firstRun": True,
                "runtimeMode": self.runtime_mode,
                "apiKeyConfigured": False,
                "adminPasswordConfigured": False,
            }

        config, sensitive = self.store.load()
        summary = {
            "firstRun": False,
            "runtimeMode": self.runtime_mode,
            "providerId": config.provider_id,
            "providerName": config.provider_name,
            "baseUrl": config.base_url,
            "model": config.model,
            "gatewayPort": config.gateway_port,
            "bindHost": config.bind_host,
            "firstRunCompleted": config.first_run_completed,
            "apiKeyConfigured": bool(sensitive.api_key),
            "adminPasswordConfigured": bool(config.admin_password),
        }
        summary["feishuChannel"] = self._feishu_channel_summary()
        summary["wechatChannel"] = self._wechat_channel_summary()
        summary["qqChannel"] = self._qq_channel_summary()
        summary["wecomChannel"] = self._wecom_channel_summary()
        return summary

    def _feishu_channel_summary(self) -> dict[str, object]:
        service = FeishuChannelService(self.paths)
        config = service.load_config()
        status = service.load_status()
        return {
            "configured": bool(config.app_id and config.app_secret),
            "enabled": config.enabled,
            "appId": self._redact(config.app_id),
            "appSecretConfigured": bool(config.app_secret),
            "botAppName": config.bot_app_name,
            "lastValidatedAt": config.last_validated_at,
            "status": status.state,
            "lastError": status.last_error,
            "lastConnectedAt": status.last_connected_at,
            "lastMessageAt": status.last_message_at,
        }

    def _wechat_channel_summary(self) -> dict[str, object]:
        service = SocialChannelService(self.paths)
        config = service.load_wechat_config()
        status = service.load_wechat_status()
        return {
            "installed": config.installed,
            "enabled": config.enabled,
            "lastLoginAt": config.last_login_at,
            "status": status.state,
            "lastError": status.last_error,
        }

    def _qq_channel_summary(self) -> dict[str, object]:
        service = SocialChannelService(self.paths)
        config = service.load_qq_config()
        status = service.load_qq_status()
        return {
            "configured": bool(config.app_id and config.app_secret),
            "enabled": config.enabled,
            "appId": self._redact(config.app_id),
            "appSecretConfigured": bool(config.app_secret),
            "lastValidatedAt": config.last_validated_at,
            "status": status.state,
            "lastError": status.last_error,
        }

    def _wecom_channel_summary(self) -> dict[str, object]:
        service = SocialChannelService(self.paths)
        config = service.load_wecom_config()
        status = service.load_wecom_status()
        return {
            "configured": bool(config.bot_id and config.secret),
            "enabled": config.enabled,
            "botId": self._redact(config.bot_id),
            "secretConfigured": bool(config.secret),
            "connectionMode": config.connection_mode,
            "lastValidatedAt": config.last_validated_at,
            "status": status.state,
            "lastError": status.last_error,
        }

    def _redact(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 6:
            return f"{value[:2]}***"
        return f"{value[:6]}***"
