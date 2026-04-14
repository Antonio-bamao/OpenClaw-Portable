from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LauncherViewState:
    status_label: str
    status_detail: str
    port_label: str
    runtime_detail: str
    provider_label: str
    message: str
    webui_url: str
    offline_mode: bool


@dataclass(frozen=True)
class FeishuChannelState:
    app_id: str
    app_secret: str
    bot_app_name: str
    enabled: bool
    status_label: str
    status_detail: str
    last_validated_at: str | None = None
    last_error: str = ""


@dataclass(frozen=True)
class WechatChannelState:
    enabled: bool
    installed: bool
    status_label: str
    status_detail: str
    last_login_at: str | None = None
    last_error: str = ""


@dataclass(frozen=True)
class QqChannelState:
    app_id: str
    app_secret: str
    enabled: bool
    status_label: str
    status_detail: str
    last_validated_at: str | None = None
    last_error: str = ""


@dataclass(frozen=True)
class WecomChannelState:
    bot_id: str
    secret: str
    enabled: bool
    connection_mode: str
    status_label: str
    status_detail: str
    last_validated_at: str | None = None
    last_error: str = ""


@dataclass(frozen=True)
class WizardStep:
    title: str
    description: str
