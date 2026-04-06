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
class WizardStep:
    title: str
    description: str
