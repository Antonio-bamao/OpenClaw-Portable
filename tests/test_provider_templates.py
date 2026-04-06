import unittest
from pathlib import Path

from launcher.services.provider_registry import ProviderTemplateRegistry


class ProviderTemplateRegistryTests(unittest.TestCase):
    def test_loads_builtin_provider_templates_from_json_directory(self) -> None:
        registry = ProviderTemplateRegistry(Path.cwd() / "state" / "provider-templates")
        templates = registry.load()

        self.assertEqual([template.identifier for template in templates], ["dashscope", "deepseek", "openrouter", "custom"])
        self.assertEqual(templates[0].display_name, "通义千问")
        self.assertEqual(templates[1].base_url, "https://api.deepseek.com/v1")


if __name__ == "__main__":
    unittest.main()
