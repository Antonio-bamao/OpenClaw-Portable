from __future__ import annotations

import os

from launcher.services.release_assets import build_latest_release_feed_url


DEFAULT_UPDATE_FEED_URL = build_latest_release_feed_url()
UPDATE_FEED_ENV_VAR = "OPENCLAW_PORTABLE_UPDATE_FEED_URL"


def resolve_update_feed_url(requested_url: str | None = None) -> str:
    url = (requested_url or os.environ.get(UPDATE_FEED_ENV_VAR) or DEFAULT_UPDATE_FEED_URL).strip()
    if not url:
        raise ValueError("更新源地址不能为空。")
    return url
