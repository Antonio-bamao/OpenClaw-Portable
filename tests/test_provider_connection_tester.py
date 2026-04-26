import json
import unittest
from io import BytesIO
from urllib.error import HTTPError, URLError

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.services.provider_connection_tester import ProviderConnectionTester


def make_config(
    *,
    provider_id: str = "dashscope",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    model: str = "qwen3.5-plus",
) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id=provider_id,
        provider_name=provider_id,
        base_url=base_url,
        model=model,
        gateway_port=18789,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


class FakeResponse:
    def __init__(self, status: int = 200, payload: bytes = b"{}") -> None:
        self.status = status
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self.payload


class ProviderConnectionTesterTests(unittest.TestCase):
    def test_posts_openai_compatible_chat_probe_without_leaking_key(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        tester = ProviderConnectionTester(urlopen=fake_urlopen)

        result = tester.test(make_config(), SensitiveConfig(api_key="sk-secret"))

        self.assertTrue(result.ok)
        self.assertEqual(captured["url"], "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-secret")
        self.assertEqual(captured["body"]["model"], "qwen3.5-plus")
        self.assertEqual(captured["body"]["max_tokens"], 1)
        self.assertNotIn("sk-secret", result.message)

    def test_posts_anthropic_messages_probe(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        tester = ProviderConnectionTester(urlopen=fake_urlopen)

        result = tester.test(
            make_config(provider_id="anthropic", base_url="https://api.anthropic.com", model="claude-sonnet-4-6"),
            SensitiveConfig(api_key="sk-ant"),
        )

        self.assertTrue(result.ok)
        self.assertEqual(captured["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(captured["headers"]["X-api-key"], "sk-ant")
        self.assertEqual(captured["headers"]["Anthropic-version"], "2023-06-01")
        self.assertEqual(captured["body"]["model"], "claude-sonnet-4-6")

    def test_reports_http_failure_without_secret(self) -> None:
        def fake_urlopen(request, timeout):
            raise HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                {},
                BytesIO(b'{"error":{"message":"bad key sk-secret"}}'),
            )

        tester = ProviderConnectionTester(urlopen=fake_urlopen)

        result = tester.test(make_config(), SensitiveConfig(api_key="sk-secret"))

        self.assertFalse(result.ok)
        self.assertIn("401", result.message)
        self.assertNotIn("sk-secret", result.message)

    def test_reports_network_failure(self) -> None:
        tester = ProviderConnectionTester(urlopen=lambda request, timeout: (_ for _ in ()).throw(URLError("offline")))

        result = tester.test(make_config(), SensitiveConfig(api_key="sk-secret"))

        self.assertFalse(result.ok)
        self.assertIn("网络", result.message)

    def test_skips_remote_probe_without_key(self) -> None:
        tester = ProviderConnectionTester(urlopen=lambda request, timeout: self.fail("must not call network"))

        result = tester.test(make_config(), SensitiveConfig(api_key=""))

        self.assertFalse(result.ok)
        self.assertIn("未提供 API Key", result.message)


if __name__ == "__main__":
    unittest.main()
