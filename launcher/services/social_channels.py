from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import hashlib
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
    last_onboarded_token_fingerprint: str | None = None


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
        return self._open_command_terminal(command)

    def open_node_script_terminal(self, script_path: Path) -> ChannelCommandResult:
        command = [self._resolved_node_command(), str(script_path)]
        return self._open_command_terminal(command)

    def _open_command_terminal(self, command: list[str]) -> ChannelCommandResult:
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
            "OPENCLAW_CONFIG_PATH": str(self.paths.runtime_config_file),
            "OPENCLAW_WORKSPACE_DIR": str(self.paths.workspace_dir),
            "OPENCLAW_LOG_DIR": str(self.paths.logs_dir),
            "OPENCLAW_CACHE_DIR": str(self.paths.cache_dir),
            "HOME": str(self.paths.state_dir),
        }


class SocialChannelService:
    def __init__(
        self,
        paths: PortablePaths,
        command_runner: OpenClawChannelCommandRunner | None = None,
        *,
        secret_loader=None,
        secret_saver=None,
    ) -> None:
        self.paths = paths
        self.command_runner = command_runner
        self._secret_loader = secret_loader
        self._secret_saver = secret_saver

    def load_wechat_config(self) -> WechatChannelConfig:
        return self._load_dataclass("wechat", "config", WechatChannelConfig)

    def save_wechat_config(self, config: WechatChannelConfig) -> None:
        self._save_dataclass("wechat", "config", config)

    def load_qq_config(self) -> QqChannelConfig:
        config = self._load_dataclass("qq", "config", QqChannelConfig)
        if not config.app_secret and self._secret_loader:
            secret = self._secret_loader("qq.appSecret")
            if secret:
                config = replace(config, app_secret=secret)
        return config

    def save_qq_config(self, config: QqChannelConfig) -> None:
        if config.app_secret and self._secret_saver:
            saved = self._secret_saver("qq.appSecret", config.app_secret)
            if saved is not False:
                config = replace(config, app_secret="")
        self._save_dataclass("qq", "config", config)

    def load_wecom_config(self) -> WecomChannelConfig:
        config = self._load_dataclass("wecom", "config", WecomChannelConfig)
        if not config.secret and self._secret_loader:
            secret = self._secret_loader("wecom.secret")
            if secret:
                config = replace(config, secret=secret)
        return config

    def save_wecom_config(self, config: WecomChannelConfig) -> None:
        if config.secret and self._secret_saver:
            saved = self._secret_saver("wecom.secret", config.secret)
            if saved is not False:
                config = replace(config, secret="")
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

    def qq_onboarding_command(self, config: QqChannelConfig) -> list[str]:
        app_id = config.app_id.strip()
        app_secret = config.app_secret.strip()
        return ["channels", "add", "--channel", "qqbot", "--token", f"{app_id}:{app_secret}"]

    def qq_token_fingerprint(self, config: QqChannelConfig) -> str | None:
        app_id = config.app_id.strip()
        app_secret = config.app_secret.strip()
        if not app_id or not app_secret:
            return None
        return hashlib.sha256(f"{app_id}:{app_secret}".encode("utf-8")).hexdigest()

    def qq_needs_onboarding(self, config: QqChannelConfig) -> bool:
        fingerprint = self.qq_token_fingerprint(config)
        if fingerprint is None:
            return False
        return config.last_onboarded_token_fingerprint != fingerprint

    def install_wechat_plugin(self) -> ChannelCommandResult:
        self._cleanup_wechat_install_staging_dirs()
        if self.wechat_runtime_plugin_available():
            config = self.load_wechat_config()
            self.save_wechat_config(replace(config, installed=True))
            self.save_wechat_status(
                SocialChannelStatus(
                    state="enabled" if config.enabled else "pending_login",
                    last_action_at=self._utc_now_iso(),
                )
            )
            return ChannelCommandResult(ok=True, output="微信 ClawBot 插件已安装。")
        self.save_wechat_status(
            SocialChannelStatus(
                state="installing",
                last_action_at=self._utc_now_iso(),
            )
        )
        result = self._run_commands(self.wechat_install_commands())
        if result.ok:
            config = self.load_wechat_config()
            self.save_wechat_config(replace(config, installed=True))
            self.save_wechat_status(SocialChannelStatus(state="pending_login", last_action_at=self._utc_now_iso()))
        else:
            if self._wechat_install_error_means_already_installed(result):
                config = self.load_wechat_config()
                self.save_wechat_config(replace(config, installed=True))
                self.save_wechat_status(
                    SocialChannelStatus(
                        state="enabled" if config.enabled else "pending_login",
                        last_action_at=self._utc_now_iso(),
                    )
                )
                return ChannelCommandResult(ok=True, output=result.output, error_message="")
            self.save_wechat_status(SocialChannelStatus(state="install_failed", last_error=result.error_message))
        return result

    def open_wechat_login_terminal(self) -> ChannelCommandResult:
        if not self.command_runner:
            return ChannelCommandResult(ok=False, error_message="OpenClaw command runner is not configured.")
        if not self.wechat_runtime_plugin_available():
            self._clear_stale_wechat_install_state("未找到微信插件文件，请重新安装微信 ClawBot 通道插件。")
            return ChannelCommandResult(
                ok=False,
                error_message="微信 ClawBot 插件未安装，请先重新安装插件。",
            )
        self.save_wechat_status(
            SocialChannelStatus(
                state="login_starting",
                last_action_at=self._utc_now_iso(),
            )
        )
        result = self.command_runner.open_node_script_terminal(self._write_wechat_login_script())
        if result.ok:
            config = self.load_wechat_config()
            self.save_wechat_config(replace(config, installed=True))
            self.save_wechat_status(SocialChannelStatus(state="pending_login", last_action_at=self._utc_now_iso()))
        else:
            self.save_wechat_status(SocialChannelStatus(state="login_failed", last_error=result.error_message))
        return result

    def confirm_wechat_runtime_login(self) -> None:
        self.refresh_wechat_runtime_status()

    def onboard_qq_channel(self, config: QqChannelConfig) -> ChannelCommandResult:
        if not self.command_runner:
            return ChannelCommandResult(ok=False, error_message="OpenClaw command runner is not configured.")
        if not self.qq_needs_onboarding(config):
            return ChannelCommandResult(ok=True, output="qqbot already onboarded")
        result = self.command_runner.run(self.qq_onboarding_command(config))
        if result.ok:
            self.save_qq_config(
                replace(
                    config,
                    last_onboarded_token_fingerprint=self.qq_token_fingerprint(config),
                )
            )
        return result

    def install_wecom_plugin(self) -> ChannelCommandResult:
        if self.wecom_runtime_plugin_available():
            self.save_wecom_status(SocialChannelStatus(state="pending_config", last_action_at=self._utc_now_iso()))
            return ChannelCommandResult(ok=True, output="企业微信插件已安装。")
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
        if config.installed and not self.wechat_runtime_plugin_available():
            self._clear_stale_wechat_install_state("未找到微信插件文件，请重新安装微信 ClawBot 通道插件。")
        config = self.load_wechat_config()
        status = self.load_wechat_status()
        label, detail = self._status_text(
            status,
            {
                "unconfigured": ("未安装", "先安装微信 ClawBot 通道插件，再打开扫码窗口完成登录。"),
                "installing": ("安装中", "正在下载并安装微信 ClawBot 插件，首次可能需要几十秒，请勿关闭窗口。"),
                "pending_login": ("待扫码", "插件已安装。点击扫码登录会打开终端二维码窗口，请等待二维码或错误日志出现。"),
                "login_starting": ("启动扫码", "正在启动微信登录窗口；如果终端短暂黑屏，请等待二维码或错误日志出现。"),
                "pending_enable": ("待启用", "扫码已完成，下一步请点击“启用微信”写入 OpenClaw 运行时配置。"),
                "enabled": ("已启用", "微信 ClawBot 通道已启用，私聊消息会进入 OpenClaw。"),
                "needs_login_check": ("需确认登录", status.last_error or "检测到新的电脑环境，请点击扫码登录确认微信登录态。"),
                "missing_runtime_plugin": ("未安装", status.last_error or "未找到微信插件文件，请重新安装微信 ClawBot 通道插件。"),
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
        if not runtime_status:
            return
        if not self._runtime_status_is_logged_in(runtime_status):
            if self._runtime_status_is_login_failed(runtime_status):
                self.save_wechat_status(
                    SocialChannelStatus(
                        state="login_failed",
                        last_error=self._runtime_status_error_message(runtime_status) or "微信扫码未完成，请重新扫码。",
                        last_action_at=self._utc_now_iso(),
                    )
                )
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
                "missing_runtime_plugin": ("缺少扩展", status.last_error or "当前便携包缺少内置 QQ Bot 扩展，请重新安装或更新 OpenClaw Portable。"),
                "pending_enable": ("待启用", "QQ Bot 凭据已保存，启用后会写入运行时配置。"),
                "enabled": ("已启用", "QQ Bot 通道已启用，可接收私聊、群聊和富媒体消息。"),
                "needs_reconnect": ("需重新启用", status.last_error or "检测到新的电脑环境，请重新启用 QQ Bot。"),
                "enable_failed": ("启用失败", status.last_error or "QQ Bot 运行时接入失败，请重试。"),
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
                "needs_reconnect": ("需重新启用", status.last_error or "检测到新的电脑环境，请重新启用企业微信。"),
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
            "last_onboarded_token_fingerprint": "lastOnboardedTokenFingerprint",
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
            "lastOnboardedTokenFingerprint": "last_onboarded_token_fingerprint",
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

    def wechat_runtime_plugin_available(self) -> bool:
        candidates = (
            self.paths.state_dir / "extensions" / "openclaw-weixin" / "openclaw.plugin.json",
            self.paths.state_dir / "extensions" / "openclaw-weixin" / "package.json",
            self.paths.state_dir / "extensions" / "openclaw-weixin" / "index.ts",
            self.paths.state_dir / "extensions" / "openclaw-weixin" / "index.js",
            self.paths.state_dir / ".openclaw" / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin" / "package.json",
            self.paths.state_dir / ".openclaw" / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin" / "dist" / "index.js",
        )
        return any(candidate.exists() for candidate in candidates)

    def wecom_runtime_plugin_available(self) -> bool:
        extension_names = (
            "wecom-openclaw-plugin",
            "openclaw-wecom",
            "wecom",
        )
        filenames = ("openclaw.plugin.json", "package.json", "index.ts", "index.js")
        return any(
            (self.paths.state_dir / "extensions" / extension_name / filename).exists()
            for extension_name in extension_names
            for filename in filenames
        )

    def _wechat_install_error_means_already_installed(self, result: ChannelCommandResult) -> bool:
        text = "\n".join(part for part in (result.output, result.error_message) if part).lower()
        return "plugin already exists" in text and "openclaw-weixin" in text

    def _clear_stale_wechat_install_state(self, message: str) -> None:
        config = self.load_wechat_config()
        self.save_wechat_config(replace(config, installed=False, enabled=False))
        self.save_wechat_status(
            SocialChannelStatus(
                state="missing_runtime_plugin",
                last_error=message,
                last_action_at=self._utc_now_iso(),
            )
        )

    def _cleanup_wechat_install_staging_dirs(self) -> None:
        extensions_dir = self.paths.state_dir / "extensions"
        if not extensions_dir.exists():
            return
        for candidate in extensions_dir.glob(".openclaw-install-stage-*"):
            if not candidate.is_dir():
                continue
            try:
                if (candidate / "index.ts").exists() or (candidate / "index.js").exists() or (candidate / "package.json").exists():
                    shutil.rmtree(candidate, ignore_errors=True)
            except OSError:
                continue

    def _write_wechat_login_script(self) -> Path:
        self.paths.ensure_directories()
        script_dir = self.paths.temp_root / "wechat-login"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / "openclaw-weixin-login.mjs"
        script_path.write_text(self._wechat_login_script_source(), encoding="utf-8")
        return script_path

    def _wechat_login_script_source(self) -> str:
        status_path = self.paths.state_dir / "channels" / "openclaw-weixin" / "status.json"
        return f"""
import fs from "node:fs";
import path from "node:path";
import {{ pathToFileURL }} from "node:url";

const stateDir = process.env.OPENCLAW_STATE_DIR || process.env.OPENCLAW_HOME;
if (!stateDir) {{
  throw new Error("OPENCLAW_STATE_DIR is not set.");
}}

const pluginRoots = [
  path.join(stateDir, ".openclaw", "npm", "node_modules", "@tencent-weixin", "openclaw-weixin"),
  path.join(stateDir, "extensions", "openclaw-weixin"),
];
const pluginRoot = pluginRoots.find((candidate) => fs.existsSync(path.join(candidate, "dist", "src", "auth", "login-qr.js")));
if (!pluginRoot) {{
  throw new Error("微信 ClawBot 插件未安装，请先在启动器里重新安装插件。");
}}

const importFile = (filePath) => import(pathToFileURL(filePath).href);
const loginModule = await importFile(path.join(pluginRoot, "dist", "src", "auth", "login-qr.js"));
const accountsModule = await importFile(path.join(pluginRoot, "dist", "src", "auth", "accounts.js"));
const sdkModule = await importFile(path.join(process.cwd(), "dist", "plugin-sdk", "account-id.js"));

const statusPath = {json.dumps(str(status_path))};
const writeStatus = (payload) => {{
  fs.mkdirSync(path.dirname(statusPath), {{ recursive: true }});
  fs.writeFileSync(statusPath, `${{JSON.stringify(payload, null, 2)}}\\n`, "utf-8");
}};

console.log("正在生成微信扫码二维码...");
const start = await loginModule.startWeixinLoginWithQr({{
  botType: loginModule.DEFAULT_ILINK_BOT_TYPE,
  force: true,
  verbose: true,
}});
if (!start.qrcodeUrl) {{
  writeStatus({{ connected: false, state: "login_failed", lastError: start.message || "二维码生成失败。" }});
  throw new Error(start.message || "二维码生成失败。");
}}

console.log(start.message || "用手机微信扫描以下二维码，以继续连接：");
await loginModule.displayQRCode(start.qrcodeUrl);
writeStatus({{
  connected: false,
  state: "pending_login",
  message: start.message || "等待扫码确认。",
  lastQrAt: new Date().toISOString(),
}});

const wait = await loginModule.waitForWeixinLogin({{
  sessionKey: start.sessionKey,
  timeoutMs: 480000,
  verbose: true,
}});
if (!wait.connected || !wait.botToken || !wait.accountId) {{
  writeStatus({{
    connected: false,
    state: "login_failed",
    lastError: wait.message || "扫码未完成。",
    updatedAt: new Date().toISOString(),
  }});
  throw new Error(wait.message || "扫码未完成。");
}}

const normalizedId = sdkModule.normalizeAccountId(wait.accountId);
accountsModule.saveWeixinAccount(normalizedId, {{
  token: wait.botToken,
  baseUrl: wait.baseUrl,
  userId: wait.userId,
}});
accountsModule.registerWeixinAccountId(normalizedId);
if (wait.userId) {{
  accountsModule.clearStaleAccountsForUserId(normalizedId, wait.userId);
}}

writeStatus({{
  connected: true,
  loggedIn: true,
  ready: true,
  accountId: normalizedId,
  lastLoginAt: new Date().toISOString(),
  message: wait.message || "已将此 OpenClaw 连接到微信。",
}});
console.log("\\n微信已连接成功，可以回到 OpenClaw Portable 点击“确认已扫码”。");
"""

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

    def _runtime_status_is_login_failed(self, payload: dict[str, object]) -> bool:
        raw_state = str(payload.get("state") or payload.get("status") or payload.get("connectionState") or "").strip()
        normalized = raw_state.lower().replace("-", "_")
        return normalized in {"login_failed", "failed", "error"} or bool(self._runtime_status_error_message(payload))

    def _runtime_status_error_message(self, payload: dict[str, object]) -> str:
        for key in ("lastError", "last_error", "error", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
