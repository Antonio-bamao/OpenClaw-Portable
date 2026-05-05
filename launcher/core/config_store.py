from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.security import SecurityService


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
    def __init__(self, paths: PortablePaths, security_service: SecurityService | None = None) -> None:
        self.paths = paths
        self.security_service = security_service or SecurityService(paths)

    def is_first_run(self) -> bool:
        return not self.paths.config_file.exists()

    def save(self, config: LauncherConfig, sensitive: SensitiveConfig) -> None:
        self.paths.ensure_directories()
        existing_config = self._load_json_object(self.paths.config_file)
        security = self.security_service
        persisted_config = config
        if config.admin_password.strip():
            if not security.is_configured():
                security.setup(config.admin_password, {"model.apiKey": sensitive.api_key})
            elif security.unlock_with_password(config.admin_password) or security.unlock_with_trusted_device():
                secrets = security.load_secrets()
                secrets["model.apiKey"] = sensitive.api_key
                security.save_secrets(secrets)
            persisted_config = replace(config, admin_password="")
            existing_config["security"] = {"enabled": True}
        elif security.is_configured() and (security.unlock_with_trusted_device()):
            secrets = security.load_secrets()
            secrets["model.apiKey"] = sensitive.api_key
            security.save_secrets(secrets)
            existing_config["security"] = {"enabled": True}
        existing_config.update(asdict(persisted_config))
        self.paths.config_file.write_text(
            json.dumps(existing_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        env_api_key = "" if security.is_configured() else sensitive.api_key
        lines = [f"OPENCLAW_API_KEY={env_api_key}".rstrip()]
        self.paths.env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def load(self) -> tuple[LauncherConfig, SensitiveConfig]:
        raw_config = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
        security = self.security_service
        api_key = ""
        if security.is_configured() and security.unlock_with_trusted_device():
            api_key = security.load_secrets().get("model.apiKey", "")
        if not api_key:
            api_key = self._read_env_value(self.paths.env_file, "OPENCLAW_API_KEY")
        sensitive = SensitiveConfig(api_key=api_key)
        launcher_keys = {field.name for field in fields(LauncherConfig)}
        launcher_config = {key: raw_config[key] for key in launcher_keys}
        launcher_config = self._migrate_launcher_config(launcher_config)
        return LauncherConfig(**launcher_config), sensitive

    def _migrate_launcher_config(self, launcher_config: dict[str, object]) -> dict[str, object]:
        migrated = dict(launcher_config)
        provider_id = str(migrated.get("provider_id", "")).strip().lower()
        model = str(migrated.get("model", "")).strip()
        if provider_id in {"dashscope", "qwen"} and model in {"qwen-max", "qwen/qwen-max"}:
            migrated["model"] = "qwen3.5-plus"
        return migrated

    def _load_json_object(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

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
