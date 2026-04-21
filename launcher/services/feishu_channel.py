from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from launcher.core.paths import PortablePaths
from launcher.models import FeishuChannelState


@dataclass(frozen=True)
class FeishuChannelConfig:
    app_id: str = ""
    app_secret: str = ""
    enabled: bool = False
    bot_app_name: str = "OpenClaw Bot"
    last_validated_at: str | None = None


@dataclass(frozen=True)
class FeishuChannelStatus:
    state: str = "unconfigured"
    last_error: str = ""
    last_connected_at: str | None = None
    last_message_at: str | None = None


@dataclass(frozen=True)
class FeishuValidationResult:
    ok: bool
    state: str
    error_message: str
    validated_at: str | None = None


@dataclass(frozen=True)
class FeishuRuntimeProjection:
    runtime_env: dict[str, str]
    runtime_config_patch: dict[str, object]


class FeishuChannelService:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def load_config(self) -> FeishuChannelConfig:
        if not self.paths.feishu_channel_config_file.exists():
            return FeishuChannelConfig()
        raw = self._load_json_object(self.paths.feishu_channel_config_file)
        return self._coerce_feishu_config(raw)

    def save_config(self, config: FeishuChannelConfig) -> None:
        self.paths.ensure_directories()
        self.paths.feishu_channel_config_file.write_text(
            json.dumps(self._to_json_keys(asdict(config)), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_status(self) -> FeishuChannelStatus:
        if not self.paths.feishu_channel_status_file.exists():
            return FeishuChannelStatus()
        raw = self._load_json_object(self.paths.feishu_channel_status_file)
        return self._coerce_feishu_status(raw)

    def save_status(self, status: FeishuChannelStatus) -> None:
        self.paths.ensure_directories()
        self.paths.feishu_channel_status_file.write_text(
            json.dumps(self._to_json_keys(asdict(status)), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def validate_credentials(self, app_id: str, app_secret: str) -> FeishuValidationResult:
        payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
        request = Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception:
            return FeishuValidationResult(
                ok=False,
                state="invalid_config",
                error_message="Feishu credential validation failed. Please check App ID / App Secret.",
            )

        if body.get("code") != 0 or not body.get("tenant_access_token"):
            return FeishuValidationResult(
                ok=False,
                state="invalid_config",
                error_message="Feishu credential validation failed. Please check App ID / App Secret.",
            )

        return FeishuValidationResult(
            ok=True,
            state="pending_enable",
            error_message="",
            validated_at=self._utc_now_iso(),
        )

    def build_runtime_projection(self, config: FeishuChannelConfig) -> FeishuRuntimeProjection:
        return FeishuRuntimeProjection(
            runtime_env={
                "FEISHU_APP_ID": config.app_id,
                "FEISHU_APP_SECRET": config.app_secret,
            },
            runtime_config_patch={
                "channels": {
                    "feishu": {
                        "defaultAccount": "default",
                        "appId": config.app_id,
                        "appSecret": config.app_secret,
                        "enabled": config.enabled,
                        "accounts": {
                            "default": {
                                "enabled": config.enabled,
                                "connectionMode": "websocket",
                            }
                        },
                    }
                }
            },
        )

    def refresh_runtime_status(
        self,
        runtime_state: str,
        runtime_message: str = "",
        channel_probe_payload: dict[str, object] | None = None,
        probe_attempted: bool = False,
        runtime_link_available: bool = True,
    ) -> FeishuChannelStatus:
        current = self.load_status()
        config = self.load_config()
        has_credentials = bool(config.app_id.strip() and config.app_secret.strip())
        probe_account = self._extract_feishu_probe_account(channel_probe_payload)

        if not has_credentials and not config.enabled:
            next_status = FeishuChannelStatus()
        elif not runtime_link_available and current.state == "invalid_config":
            next_status = current
        elif not runtime_link_available and has_credentials:
            next_status = replace(current, state="pending_enable", last_error="")
        elif has_credentials and not config.enabled:
            next_status = replace(current, state="pending_enable", last_error="")
        elif probe_account and self._probe_reports_needs_reconfigure(probe_account):
            next_status = replace(
                current,
                state="needs_reconfigure",
                last_error=self._probe_error_message(probe_account, runtime_message) or "当前飞书渠道需重新配置。",
            )
        elif probe_account and self._probe_reports_connected(probe_account):
            next_status = FeishuChannelStatus(
                state="connected",
                last_error="",
                last_connected_at=self._utc_now_iso(),
                last_message_at=current.last_message_at,
            )
        elif probe_account and self._probe_reports_failure(probe_account):
            next_status = replace(
                current,
                state="connection_failed",
                last_error=self._probe_error_message(probe_account, runtime_message) or "飞书连接失败，可查看诊断并重试",
            )
        elif probe_attempted and config.enabled and has_credentials:
            next_status = replace(
                current,
                state="connection_failed",
                last_error=runtime_message.strip() or "飞书 live probe 失败，可查看诊断并重试。",
            )
        elif runtime_state == "running" and config.enabled and has_credentials:
            next_status = FeishuChannelStatus(
                state="connected",
                last_error="",
                last_connected_at=self._utc_now_iso(),
                last_message_at=current.last_message_at,
            )
        elif runtime_state == "ready" and config.enabled:
            next_status = replace(current, state="pending_enable", last_error="")
        elif runtime_state in {"stopped", "idle"}:
            next_status = replace(current, state="pending_enable" if config.enabled else "unconfigured", last_error="")
        else:
            next_status = replace(
                current,
                state="connection_failed",
                last_error=runtime_message or "飞书连接失败，可查看诊断并重试",
            )

        self.save_status(next_status)
        return next_status

    def _extract_feishu_probe_account(self, payload: dict[str, object] | None) -> dict[str, object] | None:
        if not isinstance(payload, dict):
            return None
        accounts_by_channel = payload.get("channelAccounts")
        if not isinstance(accounts_by_channel, dict):
            return None
        raw_accounts = accounts_by_channel.get("feishu")
        if isinstance(raw_accounts, list):
            for account in raw_accounts:
                if isinstance(account, dict):
                    return account
        if isinstance(raw_accounts, dict):
            return raw_accounts
        return None

    def _probe_reports_connected(self, account: dict[str, object]) -> bool:
        probe = account.get("probe")
        return isinstance(probe, dict) and probe.get("ok") is True

    def _probe_reports_failure(self, account: dict[str, object]) -> bool:
        probe = account.get("probe")
        return isinstance(probe, dict) and probe.get("ok") is False

    def _probe_reports_needs_reconfigure(self, account: dict[str, object]) -> bool:
        configured = account.get("configured")
        return configured is False

    def _probe_error_message(self, account: dict[str, object], runtime_message: str) -> str:
        direct_error = account.get("lastError")
        if isinstance(direct_error, str) and direct_error.strip():
            return direct_error.strip()
        probe = account.get("probe")
        if isinstance(probe, dict):
            for key in ("error", "message", "reason"):
                value = probe.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return runtime_message.strip()

    def build_view_state(self) -> FeishuChannelState:
        config = self.load_config()
        status = self.load_status()
        pending_enable_detail = (
            "飞书配置已写入运行时，启动服务后会尝试建立私聊链路。"
            if config.enabled
            else "凭据已保存，启用飞书私聊后会写入运行时配置。"
        )
        labels = {
            "unconfigured": ("未配置", "填写 App ID 和 App Secret 后，先测试连接再启用飞书私聊。"),
            "invalid_config": ("配置无效", status.last_error or "配置无效，请检查 App ID / App Secret。"),
            "pending_enable": ("待启用", pending_enable_detail),
            "connecting": ("连接中", "OpenClaw 正在准备飞书私聊链路。"),
            "connected": ("已连接", "飞书私聊链路已就绪，可接收私聊消息。"),
            "connection_failed": ("连接失败", status.last_error or "飞书连接失败，可查看诊断并重试。"),
            "needs_reconfigure": ("需重新配置", status.last_error or "当前飞书渠道需重新配置。"),
        }
        label, detail = labels.get(status.state, ("未知状态", status.last_error or "飞书渠道状态暂不可用。"))
        return FeishuChannelState(
            app_id=config.app_id,
            app_secret=config.app_secret,
            bot_app_name=config.bot_app_name,
            enabled=config.enabled,
            status_label=label,
            status_detail=detail,
            last_validated_at=config.last_validated_at,
            last_error=status.last_error,
        )

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def _load_json_object(self, path: Path) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def _coerce_feishu_config(self, raw: dict[str, object]) -> FeishuChannelConfig:
        raw = self._from_json_keys(raw)
        allowed_keys = {field.name for field in fields(FeishuChannelConfig)}
        filtered = {key: raw[key] for key in allowed_keys if key in raw}
        try:
            return FeishuChannelConfig(**filtered)
        except TypeError:
            return FeishuChannelConfig()

    def _coerce_feishu_status(self, raw: dict[str, object]) -> FeishuChannelStatus:
        raw = self._from_json_keys(raw)
        allowed_keys = {field.name for field in fields(FeishuChannelStatus)}
        filtered = {key: raw[key] for key in allowed_keys if key in raw}
        try:
            return FeishuChannelStatus(**filtered)
        except TypeError:
            return FeishuChannelStatus()

    def _to_json_keys(self, payload: dict[str, object]) -> dict[str, object]:
        mapping = {
            "app_id": "appId",
            "app_secret": "appSecret",
            "bot_app_name": "botAppName",
            "last_validated_at": "lastValidatedAt",
            "last_error": "lastError",
            "last_connected_at": "lastConnectedAt",
            "last_message_at": "lastMessageAt",
        }
        return {mapping.get(key, key): value for key, value in payload.items()}

    def _from_json_keys(self, payload: dict[str, object]) -> dict[str, object]:
        mapping = {
            "appId": "app_id",
            "appSecret": "app_secret",
            "botAppName": "bot_app_name",
            "lastValidatedAt": "last_validated_at",
            "lastError": "last_error",
            "lastConnectedAt": "last_connected_at",
            "lastMessageAt": "last_message_at",
        }
        return {mapping.get(key, key): value for key, value in payload.items()}
