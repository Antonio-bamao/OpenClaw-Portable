from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from launcher.core.paths import PortablePaths


@dataclass(frozen=True)
class LauncherConfig:
    admin_password: str
    provider_id: str
    provider_name: str
    base_url: str
    model: str
    gateway_port: int
    bind_host: str
    first_run_completed: bool


@dataclass(frozen=True)
class SensitiveConfig:
    api_key: str = ""


class LauncherConfigStore:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def is_first_run(self) -> bool:
        return not self.paths.config_file.exists()

    def save(self, config: LauncherConfig, sensitive: SensitiveConfig) -> None:
        self.paths.ensure_directories()
        self.paths.config_file.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        lines = [f"OPENCLAW_API_KEY={sensitive.api_key}".rstrip()]
        self.paths.env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def load(self) -> tuple[LauncherConfig, SensitiveConfig]:
        raw_config = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
        sensitive = SensitiveConfig(api_key=self._read_env_value(self.paths.env_file, "OPENCLAW_API_KEY"))
        return LauncherConfig(**raw_config), sensitive

    def _read_env_value(self, env_path: Path, key: str) -> str:
        if not env_path.exists():
            return ""
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            current_key, value = line.split("=", 1)
            if current_key == key:
                return value
        return ""
