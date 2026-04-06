from __future__ import annotations

from dataclasses import dataclass

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.services.provider_registry import ProviderTemplate


@dataclass
class SetupWizardSession:
    provider_templates: list[ProviderTemplate]
    current_step: int = 0
    admin_password: str = ""
    selected_provider_id: str = "dashscope"
    api_key: str = ""
    gateway_port: int = 18789
    bind_host: str = "127.0.0.1"

    def next_step(self) -> None:
        self.current_step = min(self.current_step + 1, 4)

    def previous_step(self) -> None:
        self.current_step = max(self.current_step - 1, 0)

    def build_configuration(self) -> tuple[LauncherConfig, SensitiveConfig]:
        provider = self._selected_provider()
        config = LauncherConfig(
            admin_password=self.admin_password,
            provider_id=provider.identifier,
            provider_name=provider.display_name,
            base_url=provider.base_url,
            model=provider.default_model,
            gateway_port=self.gateway_port,
            bind_host=self.bind_host,
            first_run_completed=True,
        )
        return config, SensitiveConfig(api_key=self.api_key)

    def _selected_provider(self) -> ProviderTemplate:
        for template in self.provider_templates:
            if template.identifier == self.selected_provider_id:
                return template
        return self.provider_templates[0]
