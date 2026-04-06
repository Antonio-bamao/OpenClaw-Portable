from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProviderTemplate:
    identifier: str
    display_name: str
    base_url: str
    default_model: str
    order: int


class ProviderTemplateRegistry:
    def __init__(self, template_dir: Path) -> None:
        self.template_dir = template_dir

    def load(self) -> list[ProviderTemplate]:
        templates: list[ProviderTemplate] = []
        for template_path in sorted(self.template_dir.glob("*.json")):
            payload = json.loads(template_path.read_text(encoding="utf-8"))
            templates.append(
                ProviderTemplate(
                    identifier=payload["id"],
                    display_name=payload["displayName"],
                    base_url=payload["baseUrl"],
                    default_model=payload["defaultModel"],
                    order=int(payload.get("order", 999)),
                )
            )
        return sorted(templates, key=lambda item: item.order)
