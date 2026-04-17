from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.models import QqChannelState, WechatChannelState, WecomChannelState


@dataclass(frozen=True)
class SocialChannelStatus:
    state: str = "unconfigured"
    last_error: str = ""
    last_action_at: str | None = None


@dataclass(frozen=True)
class ChannelValidationResult:
    ok: bool
    state: str
    error_message: str
    validated_at: str | None = None


@dataclass(frozen=True)
class ChannelCommandResult:
    ok: bool
    output: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class SocialRuntimeProjection:
    runtime_env: dict[str, str]
    runtime_config_patch: dict[str, object]


@dataclass(frozen=True)
class WechatChannelConfig:
    enabled: bool = False
    installed: bool = False
    last_login_at: str | None = None


@dataclass(frozen=True)
class QqChannelConfig:
    app_id: str = ""
    app_secret: str = ""
    enabled: bool = False
    last_validated_at: str | None = None


@dataclass(frozen=True)
class WecomChannelConfig:
    bot_id: str = ""
    secret: str = ""
    enabled: bool = False
    connection_mode: str = "websocket"
    last_validated_at: str | None = None


class OpenClawChannelCommandRunner:
    def __init__(self, paths: PortablePaths, node_command: str = "node") -> None:
        self.paths = paths
        self.node_command = node_command

    def run(self, args: list[str], timeout_seconds: int = 180) -> ChannelCommandResult:
        try:
            completed = subprocess.run(
                self._openclaw_command(args),
                cwd=str(self._openclaw_dir()),
                env=self._environment(),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            return ChannelCommandResult(ok=False, error_message=str(exc))
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        if completed.returncode != 0:
            return ChannelCommandResult(ok=False, output=output, error_message=output.strip() or "OpenClaw command failed.")
        return ChannelCommandResult(ok=True, output=output)

    def open_interactive_terminal(self, args: list[str]) -> ChannelCommandResult:
        command = self._openclaw_command(args)
        try:
            if os.name == "nt":
                subprocess.Popen(
                    ["cmd.exe", "/k", subprocess.list2cmdline(command)],
                    cwd=str(self._openclaw_dir()),
                    env=self._environment(),
                    creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                )
            else:
                subprocess.Popen(command, cwd=str(self._openclaw_dir()), env=self._environment())
        except Exception as exc:  # noqa: BLE001
            return ChannelCommandResult(ok=False, error_message=str(exc))
        return ChannelCommandResult(ok=True)

    def _openclaw_command(self, args: list[str]) -> list[str]:
        return [self._resolved_node_command(), str(self._entrypoint_script()), *args]

    def _resolved_node_command(self) -> str:
        embedded_node = self.paths.runtime_dir / "node" / "node.exe"
        if embedded_node.exists():
            return str(embedded_node)
        return self.node_command

    def _openclaw_dir(self) -> Path:
        return self.paths.runtime_dir / "openclaw"

    def _entrypoint_script(self) -> Path:
        openclaw_dir = self._openclaw_dir()
        candidates = (
            openclaw_dir / "openclaw.mjs",
            openclaw_dir / "server.js",
            openclaw_dir / "dist" / "server.js",
            openclaw_dir / "dist" / "index.js",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return openclaw_dir / "openclaw.mjs"

    def _environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "OPENCLAW_HOME": str(self.paths.state_dir),
            "OPENCLAW_STATE_DIR": str(self.paths.state_dir),
            "OPENCLAW_CONFIG_PATH": str(self.paths.config_file),
            "OPENCLAW_WORKSPACE_DIR": str(self.paths.workspace_dir),
            "OPENCLAW_LOG_DIR": str(self.paths.logs_dir),
            "OPENCLAW_CACHE_DIR": str(self.paths.cache_dir),
            "HOME": str(self.paths.state_dir),
        }


class SocialChannelService:
    def __init__(self, paths: PortablePaths, command_runner: OpenClawChannelCommandRunner | None = None) -> None:
        self.paths = paths
        self.command_runner = command_runner

    def load_wechat_config(self) -> WechatChannelConfig:
        return self._load_dataclass("wechat", "config", WechatChannelConfig)

    def save_wechat_config(self, config: WechatChannelConfig) -> None:
        self._save_dataclass("wechat", "config", config)

    def load_qq_config(self) -> QqChannelConfig:
        return self._load_dataclass("qq", "config", QqChannelConfig)

    def save_qq_config(self, config: QqChannelConfig) -> None:
        self._save_dataclass("qq", "config", config)

    def load_wecom_config(self) -> WecomChannelConfig:
        return self._load_dataclass("wecom", "config", WecomChannelConfig)

    def save_wecom_config(self, config: WecomChannelConfig) -> None:
        self._save_dataclass("wecom", "config", config)

    def load_wechat_status(self) -> SocialChannelStatus:
        return self._load_dataclass("wechat", "status", SocialChannelStatus)

    def save_wechat_status(self, status: SocialChannelStatus) -> None:
        self._save_dataclass("wechat", "status", status)

    def load_qq_status(self) -> SocialChannelStatus:
        return self._load_dataclass("qq", "status", SocialChannelStatus)

    def save_qq_status(self, status: SocialChannelStatus) -> None:
        self._save_dataclass("qq", "status", status)

    def load_wecom_status(self) -> SocialChannelStatus:
        return self._load_dataclass("wecom", "status", SocialChannelStatus)

    def save_wecom_status(self, status: SocialChannelStatus) -> None:
        self._save_dataclass("wecom", "status", status)

    def wechat_install_commands(self) -> list[list[str]]:
        return [
            ["plugins", "install", "@tencent-weixin/openclaw-weixin@latest"],
            ["config", "set", "plugins.entries.openclaw-weixin.enabled", "true"],
        ]

    def wechat_login_command(self) -> list[str]:
        return ["channels", "login", "--channel", "openclaw-weixin"]

    def wecom_install_commands(self) -> list[list[str]]:
        return [["plugins", "install", "@wecom/wecom-openclaw-plugin@latest"]]

    def install_wechat_plugin(self) -> ChannelCommandResult:
        result = self._run_commands(self.wechat_install_commands())
        if result.ok:
            config = self.load_wechat_config()
            self.save_wechat_config(replace(config, installed=True))
            self.save_wechat_status(SocialChannelStatus(state="pending_login", last_action_at=self._utc_now_iso()))
        else:
            self.save_wechat_status(SocialChannelStatus(state="install_failed", last_error=result.error_message))
        return result

    def open_wechat_login_terminal(self) -> ChannelCommandResult:
        if not self.command_runner:
            return ChannelCommandResult(ok=False, error_message="OpenClaw command runner is not configured.")
        result = self.command_runner.open_interactive_terminal(self.wechat_login_command())
        if result.ok:
            config = self.load_wechat_config()
            self.save_wechat_config(replace(config, last_login_at=self._utc_now_iso()))
            self.save_wechat_status(SocialChannelStatus(state="pending_enable", last_action_at=self._utc_now_iso()))
        else:
            self.save_wechat_status(SocialChannelStatus(state="login_failed", last_error=result.error_message))
        return result

    def install_wecom_plugin(self) -> ChannelCommandResult:
        result = self._run_commands(self.wecom_install_commands())
        if result.ok:
            self.save_wecom_status(SocialChannelStatus(state="pending_config", last_action_at=self._utc_now_iso()))
        else:
            self.save_wecom_status(SocialChannelStatus(state="install_failed", last_error=result.error_message))
        return result

    def validate_qq_config(self, config: QqChannelConfig) -> ChannelValidationResult:
        if not config.app_id.strip() or not config.app_secret.strip():
            return ChannelValidationResult(False, "invalid_config", "请填写 QQ Bot 的 AppID 和 AppSecret。")
        if not self.qq_runtime_plugin_available():
            return ChannelValidationResult(False, "missing_runtime_plugin", "当前便携包缺少内置 QQ Bot 扩展，请重新安装或更新 OpenClaw Portable。")
        return ChannelValidationResult(True, "pending_enable", "", self._utc_now_iso())

    def validate_wecom_config(self, config: WecomChannelConfig) -> ChannelValidationResult:
        if not config.bot_id.strip() or not config.secret.strip():
            return ChannelValidationResult(False, "invalid_config", "请填写企业微信 Bot ID 和 Secret。")
        return ChannelValidationResult(True, "pending_enable", "", self._utc_now_iso())

    def build_wechat_runtime_projection(self, config: WechatChannelConfig) -> SocialRuntimeProjection:
        return SocialRuntimeProjection(
            runtime_env={},
            runtime_config_patch={
                "plugins": {
                    "entries": {
                        "openclaw-weixin": {
                            "enabled": config.enabled,
                        }
                    }
                },
                "channels": {
                    "openclaw-weixin": {
                        "enabled": config.enabled,
                    }
                },
            },
        )

    def build_qq_runtime_projection(self, config: QqChannelConfig) -> SocialRuntimeProjection:
        app_id = config.app_id.strip()
        app_secret = config.app_secret.strip()
        return SocialRuntimeProjection(
            runtime_env={
                "QQBOT_APP_ID": app_id,
                "QQBOT_CLIENT_SECRET": app_secret,
            }
            if app_id and app_secret
            else {},
            runtime_config_patch={
                "channels": {
                    "qqbot": {
                        "defaultAccount": "default",
                        "enabled": config.enabled,
                        "appId": app_id,
                        "clientSecret": app_secret,
                        "accounts": {
                            "default": {
                                "enabled": config.enabled,
                                "appId": app_id,
                                "clientSecret": app_secret,
                            }
                        },
                    }
                }
            },
        )

    def build_wecom_runtime_projection(self, config: WecomChannelConfig) -> SocialRuntimeProjection:
        return SocialRuntimeProjection(
            runtime_env={},
            runtime_config_patch={
                "channels": {
                    "wecom": {
                        "enabled": config.enabled,
                        "botId": config.bot_id,
                        "secret": config.secret,
                        "connectionMode": config.connection_mode or "websocket",
                    }
                }
            },
        )

    def build_view_states(self) -> tuple[WechatChannelState, QqChannelState, WecomChannelState]:
        return (self.build_wechat_view_state(), self.build_qq_view_state(), self.build_wecom_view_state())

    def build_wechat_view_state(self) -> WechatChannelState:
        self.refresh_wechat_runtime_status()
        config = self.load_wechat_config()
        status = self.load_wechat_status()
        label, detail = self._status_text(
            status,
            {
                "unconfigured": ("未安装", "先安装微信 ClawBot 通道插件，再打开扫码窗口完成登录。"),
                "pending_login": ("待扫码", "插件已安装，点击扫码登录会打开二维码窗口。"),
                "pending_enable": ("待启用", "扫码流程已启动，启用后会写入 OpenClaw 运行时配置。"),
                "enabled": ("已启用", "微信 ClawBot 通道已启用，私聊消息会进入 OpenClaw。"),
                "install_failed": ("安装失败", status.last_error or "微信插件安装失败，请检查网络或运行时。"),
                "login_failed": ("扫码失败", status.last_error or "扫码窗口启动失败，请重试。"),
            },
        )
        return WechatChannelState(
            enabled=config.enabled,
            installed=config.installed,
            status_label=label,
            status_detail=detail,
            last_login_at=config.last_login_at,
            last_error=status.last_error,
        )

    def refresh_wechat_runtime_status(self) -> None:
        runtime_status = self._load_wechat_runtime_status()
        if not runtime_status or not self._runtime_status_is_logged_in(runtime_status):
            return
        config = self.load_wechat_config()
        last_login_at = str(
            runtime_status.get("lastLoginAt")
            or runtime_status.get("last_login_at")
            or runtime_status.get("loggedInAt")
            or config.last_login_at
            or self._utc_now_iso()
        )
        self.save_wechat_config(replace(config, installed=True, last_login_at=last_login_at))
        self.save_wechat_status(
            SocialChannelStatus(
                state="enabled" if config.enabled else "pending_enable",
                last_action_at=self._utc_now_iso(),
            )
        )

    def build_qq_view_state(self) -> QqChannelState:
        config = self.load_qq_config()
        status = self.load_qq_status()
        label, detail = self._status_text(
            status,
            {
                "unconfigured": ("未配置", "在 QQ 开放平台创建机器人后，填入 AppID 和 AppSecret。"),
                "invalid_config": ("配置无效", status.last_error or "请检查 QQ Bot 的 AppID 和 AppSecret。"),
                "pending_enable": ("待启用", "QQ Bot 凭据已保存，启用后会写入运行时配置。"),
                "enabled": ("已启用", "QQ Bot 通道已启用，可接收私聊、群聊和富媒体消息。"),
            },
        )
        return QqChannelState(config.app_id, config.app_secret, config.enabled, label, detail, config.last_validated_at, status.last_error)

    def build_wecom_view_state(self) -> WecomChannelState:
        config = self.load_wecom_config()
        status = self.load_wecom_status()
        label, detail = self._status_text(
            status,
            {
                "unconfigured": ("未配置", "先安装企业微信插件，再填入 Bot ID 和 Secret。"),
                "pending_config": ("待配置", "企业微信插件已安装，请填写 Bot ID 和 Secret。"),
                "invalid_config": ("配置无效", status.last_error or "请检查企业微信 Bot ID 和 Secret。"),
                "pending_enable": ("待启用", "企业微信凭据已保存，启用后会写入运行时配置。"),
                "enabled": ("已启用", "企业微信通道已启用。"),
                "install_failed": ("安装失败", status.last_error or "企业微信插件安装失败，请检查网络或运行时。"),
            },
        )
        return WecomChannelState(
            config.bot_id,
            config.secret,
            config.enabled,
            config.connection_mode,
            label,
            detail,
            config.last_validated_at,
            status.last_error,
        )

    def _run_commands(self, commands: list[list[str]]) -> ChannelCommandResult:
        if not self.command_runner:
            return ChannelCommandResult(ok=False, error_message="OpenClaw command runner is not configured.")
        output_parts: list[str] = []
        for command in commands:
            result = self.command_runner.run(command)
            if result.output:
                output_parts.append(result.output)
            if not result.ok:
                return ChannelCommandResult(ok=False, output="\n".join(output_parts), error_message=result.error_message)
        return ChannelCommandResult(ok=True, output="\n".join(output_parts))

    def _load_dataclass(self, channel: str, kind: str, model):
        path = self._channel_file(channel, kind)
        if not path.exists():
            return model()
        raw = self._load_json_object(path)
        raw = self._from_json_keys(raw)
        allowed_keys = {field.name for field in fields(model)}
        filtered = {key: raw[key] for key in allowed_keys if key in raw}
        try:
            return model(**filtered)
        except TypeError:
            return model()

    def _save_dataclass(self, channel: str, kind: str, value: object) -> None:
        self.paths.ensure_directories()
        channel_dir = self.paths.state_dir / "channels" / channel
        channel_dir.mkdir(parents=True, exist_ok=True)
        path = self._channel_file(channel, kind)
        path.write_text(json.dumps(self._to_json_keys(asdict(value)), ensure_ascii=False, indent=2), encoding="utf-8")

    def _channel_file(self, channel: str, kind: str) -> Path:
        return self.paths.state_dir / "channels" / channel / f"{kind}.json"

    def _load_json_object(self, path: Path) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def _to_json_keys(self, payload: dict[str, object]) -> dict[str, object]:
        mapping = {
            "app_id": "appId",
            "app_secret": "appSecret",
            "last_validated_at": "lastValidatedAt",
            "last_login_at": "lastLoginAt",
            "last_error": "lastError",
            "last_action_at": "lastActionAt",
            "bot_id": "botId",
            "connection_mode": "connectionMode",
        }
        return {mapping.get(key, key): value for key, value in payload.items()}

    def _from_json_keys(self, payload: dict[str, object]) -> dict[str, object]:
        mapping = {
            "appId": "app_id",
            "appSecret": "app_secret",
            "lastValidatedAt": "last_validated_at",
            "lastLoginAt": "last_login_at",
            "lastError": "last_error",
            "lastActionAt": "last_action_at",
            "botId": "bot_id",
            "connectionMode": "connection_mode",
        }
        return {mapping.get(key, key): value for key, value in payload.items()}

    def _status_text(self, status: SocialChannelStatus, labels: dict[str, tuple[str, str]]) -> tuple[str, str]:
        return labels.get(status.state, ("未知状态", status.last_error or "渠道状态暂不可用。"))

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def qq_runtime_plugin_available(self) -> bool:
        openclaw_dir = self.paths.runtime_dir / "openclaw"
        if not openclaw_dir.exists():
            return True
        candidates = (
            openclaw_dir / "dist" / "extensions" / "qqbot" / "openclaw.plugin.json",
            openclaw_dir / "dist" / "extensions" / "qqbot" / "index.js",
            openclaw_dir / "dist" / "extensions" / "qqbot",
        )
        return any(candidate.exists() for candidate in candidates)

    def _load_wechat_runtime_status(self) -> dict[str, object]:
        candidates = (
            self.paths.state_dir / "channels" / "openclaw-weixin" / "status.json",
            self.paths.state_dir / "channels" / "weixin" / "status.json",
            self.paths.state_dir / "openclaw-weixin" / "status.json",
        )
        for candidate in candidates:
            payload = self._load_json_object(candidate)
            if payload:
                return payload
        return {}

    def _runtime_status_is_logged_in(self, payload: dict[str, object]) -> bool:
        for key in ("loggedIn", "authenticated", "connected", "ready"):
            value = payload.get(key)
            if isinstance(value, bool) and value:
                return True
        raw_state = str(payload.get("state") or payload.get("status") or payload.get("connectionState") or "").strip()
        normalized = raw_state.lower().replace("-", "_")
        return normalized in {"logged_in", "connected", "ready", "online", "authenticated"}
