import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.services.provider_bridge import ProviderBridge


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"provider-bridge-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config(
    *,
    provider_id: str,
    provider_name: str,
    base_url: str,
    model: str,
) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=base_url,
        model=model,
        gateway_port=18789,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


class ProviderBridgeTests(unittest.TestCase):
    def test_detects_qwen_from_dashscope_and_generates_runtime_primary_model(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="dashscope",
                    provider_name="通义千问",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-max",
                ),
                SensitiveConfig(api_key="sk-qwen"),
            )

            self.assertEqual(projection.provider_type, "qwen")
            self.assertEqual(projection.primary_model, "qwen/qwen-max")
            self.assertEqual(
                projection.runtime_config_patch["agents"]["defaults"]["model"]["primary"],
                "qwen/qwen-max",
            )
            self.assertEqual(projection.auth_profile_id, "qwen:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_detects_openai_from_provider_id(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            self.assertEqual(projection.provider_type, "openai")
            self.assertEqual(projection.primary_model, "openai/gpt-5.4")
            self.assertEqual(projection.auth_profile_id, "openai:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_detects_anthropic_from_api_base(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="anthropic",
                    provider_name="Anthropic",
                    base_url="https://api.anthropic.com",
                    model="claude-sonnet-4-6",
                ),
                SensitiveConfig(api_key="sk-ant"),
            )

            self.assertEqual(projection.provider_type, "anthropic")
            self.assertEqual(projection.primary_model, "anthropic/claude-sonnet-4-6")
            self.assertEqual(projection.auth_profile_id, "anthropic:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_falls_back_to_custom_compatible_for_unknown_openai_style_endpoint(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="custom",
                    provider_name="自定义",
                    base_url="https://llm.example.com/v1",
                    model="acme-chat-pro",
                ),
                SensitiveConfig(api_key="sk-custom"),
            )

            self.assertEqual(projection.provider_type, "custom-compatible")
            self.assertEqual(projection.auth_profile_id, "custom-compatible:launcher")
            self.assertIn("models", projection.runtime_config_patch)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_apply_writes_launcher_owned_main_agent_auth_profile(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            payload = json.loads(paths.main_agent_auth_profiles_file.read_text(encoding="utf-8"))
            self.assertIn("profiles", payload)
            self.assertIn("openai:launcher", payload["profiles"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_apply_preserves_unrelated_auth_profiles(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            paths.main_agent_auth_profiles_file.parent.mkdir(parents=True, exist_ok=True)
            paths.main_agent_auth_profiles_file.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "anthropic:manual": {
                                "provider": "anthropic",
                                "api_key": {"key": "sk-manual"},
                            }
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            payload = json.loads(paths.main_agent_auth_profiles_file.read_text(encoding="utf-8"))
            self.assertIn("anthropic:manual", payload["profiles"])
            self.assertIn("openai:launcher", payload["profiles"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_apply_skips_auth_profile_write_when_api_key_is_empty(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="dashscope",
                    provider_name="通义千问",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-max",
                ),
                SensitiveConfig(api_key=""),
            )

            self.assertFalse(paths.main_agent_auth_profiles_file.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
