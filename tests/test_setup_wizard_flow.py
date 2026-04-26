import unittest

from launcher.services.provider_registry import ProviderTemplate
from launcher.services.setup_wizard import SetupWizardSession


def make_templates() -> list[ProviderTemplate]:
    return [
        ProviderTemplate("dashscope", "通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-max", 10),
        ProviderTemplate("deepseek", "DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat", 20),
        ProviderTemplate("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4.1-mini", 30),
        ProviderTemplate("openai", "OpenAI", "https://api.openai.com/v1", "gpt-5.4", 40),
        ProviderTemplate("anthropic", "Anthropic", "https://api.anthropic.com", "claude-sonnet-4-6", 50),
        ProviderTemplate("custom", "自定义", "", "", 99),
    ]


class SetupWizardSessionTests(unittest.TestCase):
    def test_moves_between_steps_with_bounds(self) -> None:
        session = SetupWizardSession(make_templates())

        self.assertEqual(session.current_step, 0)
        session.next_step()
        session.next_step()
        self.assertEqual(session.current_step, 2)
        session.previous_step()
        self.assertEqual(session.current_step, 1)

        for _ in range(10):
            session.next_step()
        self.assertEqual(session.current_step, 4)

    def test_builds_launcher_configuration_and_sensitive_payload(self) -> None:
        session = SetupWizardSession(make_templates())
        session.admin_password = "demo-pass"
        session.selected_provider_id = "deepseek"
        session.api_key = "sk-demo"
        session.gateway_port = 18889

        config, sensitive = session.build_configuration()

        self.assertEqual(config.provider_id, "deepseek")
        self.assertEqual(config.provider_name, "DeepSeek")
        self.assertEqual(config.base_url, "https://api.deepseek.com/v1")
        self.assertEqual(config.model, "deepseek-chat")
        self.assertEqual(config.gateway_port, 18889)
        self.assertEqual(sensitive.api_key, "sk-demo")

    def test_supports_offline_mode_when_api_key_is_empty(self) -> None:
        session = SetupWizardSession(make_templates())
        session.admin_password = "demo-pass"

        config, sensitive = session.build_configuration()

        self.assertEqual(config.provider_id, "dashscope")
        self.assertEqual(sensitive.api_key, "")

    def test_builds_openai_configuration_from_selected_template(self) -> None:
        session = SetupWizardSession(make_templates())
        session.selected_provider_id = "openai"
        session.api_key = "sk-openai"

        config, sensitive = session.build_configuration()

        self.assertEqual(config.provider_id, "openai")
        self.assertEqual(config.model, "gpt-5.4")
        self.assertEqual(sensitive.api_key, "sk-openai")


if __name__ == "__main__":
    unittest.main()
