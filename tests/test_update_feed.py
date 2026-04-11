import os
import unittest
from unittest.mock import patch

from launcher.services.update_feed import DEFAULT_UPDATE_FEED_URL, resolve_update_feed_url


class UpdateFeedResolutionTests(unittest.TestCase):
    def test_default_update_feed_url_points_to_latest_release_update_json(self) -> None:
        self.assertEqual(
            DEFAULT_UPDATE_FEED_URL,
            "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json",
        )

    def test_resolve_update_feed_url_uses_default_when_no_override_exists(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENCLAW_PORTABLE_UPDATE_FEED_URL", None)

            url = resolve_update_feed_url()

        self.assertEqual(url, DEFAULT_UPDATE_FEED_URL)

    def test_resolve_update_feed_url_prefers_environment_override(self) -> None:
        with patch.dict(os.environ, {"OPENCLAW_PORTABLE_UPDATE_FEED_URL": "https://staging.example.com/update.json"}, clear=False):
            url = resolve_update_feed_url()

        self.assertEqual(url, "https://staging.example.com/update.json")

    def test_resolve_update_feed_url_prefers_explicit_url_over_environment_override(self) -> None:
        with patch.dict(os.environ, {"OPENCLAW_PORTABLE_UPDATE_FEED_URL": "https://staging.example.com/update.json"}, clear=False):
            url = resolve_update_feed_url("https://prod.example.com/update.json")

        self.assertEqual(url, "https://prod.example.com/update.json")


if __name__ == "__main__":
    unittest.main()
