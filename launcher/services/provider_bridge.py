from __future__ import annotations

from dataclasses import dataclass

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths


@dataclass(frozen=True)
class ProviderBridgeProjection:
    provider_type: str
    primary_model: str
    runtime_config_patch: dict[str, object]
    auth_profile_id: str | None
    auth_profiles_document: dict[str, object] | None


class ProviderBridge:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def build_projection(
        self,
        config: LauncherConfig,
        sensitive: SensitiveConfig,
    ) -> ProviderBridgeProjection:
        provider_type = self._detect_provider_type(config)
        primary_model = self._resolve_primary_model(provider_type, config.model)
        runtime_patch = self._build_runtime_patch(provider_type, config, primary_model)
        auth_profile_id, auth_doc = self._build_auth_document(provider_type, sensitive.api_key)
        return ProviderBridgeProjection(
            provider_type=provider_type,
            primary_model=primary_model,
            runtime_config_patch=runtime_patch,
            auth_profile_id=auth_profile_id,
            auth_profiles_document=auth_doc,
        )

    def apply(self, config: LauncherConfig, sensitive: SensitiveConfig) -> ProviderBridgeProjection:
        projection = self.build_projection(config, sensitive)
        self.paths.ensure_directories()
        if projection.auth_profiles_document is not None:
            self._save_auth_profiles_document(projection.auth_profiles_document)
        return projection

    def _detect_provider_type(self, config: LauncherConfig) -> str:
        provider_id = config.provider_id.strip().lower()
        provider_from_id = self._provider_type_from_id(provider_id)
        if provider_from_id:
            return provider_from_id

        base_url = config.base_url.strip().lower()
        provider_from_url = self._provider_type_from_url(base_url)
        if provider_from_url:
            return provider_from_url

        model = config.model.strip().lower()
        provider_from_model = self._provider_type_from_model(model)
        if provider_from_model:
            return provider_from_model

        return "custom-compatible"

    def _provider_type_from_id(self, provider_id: str) -> str | None:
        provider_ids = {
            "openai": "openai",
            "anthropic": "anthropic",
            "dashscope": "qwen",
            "qwen": "qwen",
            "deepseek": "deepseek",
            "openrouter": "openrouter",
        }
        return provider_ids.get(provider_id)

    def _provider_type_from_url(self, base_url: str) -> str | None:
        if "api.openai.com" in base_url:
            return "openai"
        if "api.anthropic.com" in base_url:
            return "anthropic"
        if "dashscope.aliyuncs.com" in base_url:
            return "qwen"
        if "api.deepseek.com" in base_url:
            return "deepseek"
        if "openrouter.ai" in base_url:
            return "openrouter"
        return None

    def _provider_type_from_model(self, model: str) -> str | None:
        if model.startswith("openai/") or model.startswith("gpt-"):
            return "openai"
        if model.startswith("anthropic/") or model.startswith("claude-"):
            return "anthropic"
        if model.startswith("qwen/") or model.startswith("qwen-"):
            return "qwen"
        if model.startswith("deepseek/") or model.startswith("deepseek-"):
            return "deepseek"
        if model.startswith("openrouter/"):
            return "openrouter"
        return None

    def _resolve_primary_model(self, provider_type: str, model: str) -> str:
        normalized_model = model.strip()
        if "/" in normalized_model:
            return normalized_model
        return f"{provider_type}/{normalized_model}"

    def _build_runtime_patch(
        self,
        provider_type: str,
        config: LauncherConfig,
        primary_model: str,
    ) -> dict[str, object]:
        patch: dict[str, object] = {
            "agents": {
                "defaults": {
                    "model": {
                        "primary": primary_model,
                    },
                },
            },
        }
        if provider_type == "custom-compatible":
            patch["models"] = {
                "providers": {
                    "custom-compatible": {
                        "type": "openai-compatible",
                        "baseUrl": config.base_url.strip(),
                        "models": [config.model.strip()],
                    },
                },
            }
        return patch

    def _build_auth_document(
        self,
        provider_type: str,
        api_key: str,
    ) -> tuple[str | None, dict[str, object] | None]:
        normalized_api_key = api_key.strip()
        if not normalized_api_key:
            return None, None

        profile_id = f"{provider_type}:launcher"
        return profile_id, {
            "profiles": {
                profile_id: {
                    "provider": provider_type,
                    "api_key": {
                        "key": normalized_api_key,
                    },
                },
            },
        }

    def _save_auth_profiles_document(self, launcher_document: dict[str, object]) -> None:
        self.paths.main_agent_auth_profiles_file.parent.mkdir(parents=True, exist_ok=True)
