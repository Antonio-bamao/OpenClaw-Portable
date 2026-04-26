from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from launcher.core.config_store import LauncherConfig, SensitiveConfig


@dataclass(frozen=True)
class ProviderConnectionTestResult:
    ok: bool
    message: str


class ProviderConnectionTester:
    def __init__(self, *, urlopen: Callable | None = None, timeout_seconds: int = 20) -> None:
        self._urlopen = urlopen or globals()["urlopen"]
        self._timeout_seconds = timeout_seconds

    def test(self, config: LauncherConfig, sensitive: SensitiveConfig) -> ProviderConnectionTestResult:
        api_key = sensitive.api_key.strip()
        if not api_key:
            return ProviderConnectionTestResult(False, "未提供 API Key，将以离线模式继续。")

        try:
            request = self._build_request(config, api_key)
            with self._urlopen(request, timeout=self._timeout_seconds) as response:
                status = int(getattr(response, "status", 200) or 200)
                if 200 <= status < 300:
                    return ProviderConnectionTestResult(True, "连接测试通过：Provider、API Key 和模型接口均可访问。")
                return ProviderConnectionTestResult(False, f"连接测试失败：HTTP {status}。")
        except HTTPError as error:
            detail = self._read_http_error_detail(error, api_key)
            suffix = f"：{detail}" if detail else ""
            return ProviderConnectionTestResult(False, f"连接测试失败：HTTP {error.code}{suffix}")
        except URLError as error:
            return ProviderConnectionTestResult(False, f"连接测试失败：网络不可达或 TLS 连接失败（{self._redact(str(error.reason), api_key)}）。")
        except TimeoutError:
            return ProviderConnectionTestResult(False, "连接测试失败：请求超时。")
        except Exception as error:
            return ProviderConnectionTestResult(False, f"连接测试失败：{self._redact(str(error), api_key)}")

    def _build_request(self, config: LauncherConfig, api_key: str) -> Request:
        provider_id = config.provider_id.strip().lower()
        if provider_id == "anthropic" or "api.anthropic.com" in config.base_url.lower():
            return self._build_anthropic_request(config, api_key)
        return self._build_openai_compatible_request(config, api_key)

    def _build_openai_compatible_request(self, config: LauncherConfig, api_key: str) -> Request:
        payload = {
            "model": self._request_model_id(config),
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "stream": False,
        }
        return self._json_request(
            urljoin(self._base_url(config.base_url), "chat/completions"),
            payload,
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def _build_anthropic_request(self, config: LauncherConfig, api_key: str) -> Request:
        payload = {
            "model": self._request_model_id(config),
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }
        return self._json_request(
            urljoin(self._base_url(config.base_url), "v1/messages"),
            payload,
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    def _json_request(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> Request:
        return Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def _request_model_id(self, config: LauncherConfig) -> str:
        model = config.model.strip()
        if config.provider_id.strip().lower() == "dashscope" and model == "qwen-max":
            return "qwen3.5-plus"
        if "/" in model and not model.startswith("openai/"):
            return model.split("/", 1)[1]
        return model

    def _base_url(self, base_url: str) -> str:
        clean = base_url.strip()
        if not clean.endswith("/"):
            clean = f"{clean}/"
        return clean

    def _read_http_error_detail(self, error: HTTPError, api_key: str) -> str:
        try:
            raw = error.read().decode("utf-8", errors="replace")
        except Exception:
            return ""
        redacted = self._redact(raw, api_key).strip()
        if not redacted:
            return ""
        try:
            payload = json.loads(redacted)
        except json.JSONDecodeError:
            return redacted[:240]
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str):
                return message[:240]
            error_payload = payload.get("error")
            if isinstance(error_payload, dict):
                error_message = error_payload.get("message")
                if isinstance(error_message, str):
                    return error_message[:240]
        return redacted[:240]

    def _redact(self, value: str, api_key: str) -> str:
        if not api_key:
            return value
        return value.replace(api_key, "[redacted]")
