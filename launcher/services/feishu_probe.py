from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from launcher.core.paths import PortablePaths
from launcher.services.feishu_channel import FeishuChannelService
from launcher.services.social_channels import OpenClawChannelCommandRunner


@dataclass(frozen=True)
class FeishuProbeEvidence:
    collected_at: str
    account_id: str
    configured: bool | None
    enabled: bool | None
    probe_ok: bool | None
    bot_username: str
    last_error: str
    source: str = "openclaw channels status --probe --json"

    @property
    def ok(self) -> bool:
        return self.probe_ok is True and self.configured is not False and self.enabled is not False

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "ok": self.ok,
            "channel": "feishu",
        }


def verify_feishu_channel(
    paths: PortablePaths,
    *,
    command_runner: OpenClawChannelCommandRunner | None = None,
    timeout_seconds: int = 30,
) -> FeishuProbeEvidence:
    config = FeishuChannelService(paths).load_config()
    if not config.enabled:
        raise ValueError("Feishu channel is not enabled in local launcher state.")
    if not config.app_id.strip() or not config.app_secret.strip():
        raise ValueError("Feishu channel is not fully configured in local launcher state.")

    runner = command_runner or OpenClawChannelCommandRunner(paths)
    result = runner.run(["channels", "status", "--probe", "--json"], timeout_seconds=timeout_seconds)
    if not result.ok:
        message = result.error_message.strip() or result.output.strip() or "Feishu probe command failed."
        raise RuntimeError(message)

    payload = parse_json_object(result.output)
    if payload is None:
        raise ValueError("Feishu probe command did not return a JSON object.")
    return build_feishu_probe_evidence(payload)


def build_feishu_probe_evidence(
    payload: dict[str, object] | None,
    *,
    collected_at: str | None = None,
) -> FeishuProbeEvidence:
    account = _extract_feishu_probe_account(payload)
    if account is None:
        raise ValueError("Feishu probe payload does not include channelAccounts.feishu.")

    probe = account.get("probe")
    probe_ok = probe.get("ok") if isinstance(probe, dict) and isinstance(probe.get("ok"), bool) else None
    raw_username = ""
    if isinstance(probe, dict):
        bot = probe.get("bot")
        if isinstance(bot, dict):
            raw_username = str(bot.get("username") or "").strip()
    bot_username = ""
    if raw_username:
        bot_username = raw_username if raw_username.startswith("@") else f"@{raw_username}"

    return FeishuProbeEvidence(
        collected_at=collected_at or _utc_now_iso(),
        account_id=str(account.get("accountId") or "default"),
        configured=account.get("configured") if isinstance(account.get("configured"), bool) else None,
        enabled=account.get("enabled") if isinstance(account.get("enabled"), bool) else None,
        probe_ok=probe_ok,
        bot_username=bot_username,
        last_error=_probe_error_message(account),
    )


def parse_json_object(raw_output: str) -> dict[str, object] | None:
    trimmed = raw_output.strip()
    if not trimmed:
        return None
    candidates = [trimmed]
    if "{" in trimmed and "}" in trimmed:
        candidates.append(trimmed[trimmed.find("{") : trimmed.rfind("}") + 1])
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _extract_feishu_probe_account(payload: dict[str, object] | None) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    accounts_by_channel = payload.get("channelAccounts")
    if not isinstance(accounts_by_channel, dict):
        return None
    raw_accounts = accounts_by_channel.get("feishu")
    if isinstance(raw_accounts, list):
        for account in raw_accounts:
            if isinstance(account, dict):
                return account
    if isinstance(raw_accounts, dict):
        return raw_accounts
    return None


def _probe_error_message(account: dict[str, object]) -> str:
    direct_error = account.get("lastError")
    if isinstance(direct_error, str) and direct_error.strip():
        return direct_error.strip()
    probe = account.get("probe")
    if isinstance(probe, dict):
        for key in ("error", "message", "reason"):
            value = probe.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
