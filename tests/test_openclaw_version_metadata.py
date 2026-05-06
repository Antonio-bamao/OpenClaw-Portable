import json
import re
import unittest
from pathlib import Path


class OpenClawVersionMetadataTests(unittest.TestCase):
    def test_portable_release_version_matches_build_month(self) -> None:
        version_info = json.loads(Path("version.json").read_text(encoding="utf-8"))

        release_match = re.fullmatch(r"v(\d{4})\.(\d{2})\.(\d+)", version_info["version"])
        build_date_match = re.fullmatch(
            r"(\d{4})-(\d{2})-\d{2}",
            version_info["buildDate"],
        )

        self.assertIsNotNone(release_match)
        self.assertIsNotNone(build_date_match)
        self.assertEqual(build_date_match.group(1), release_match.group(1))
        self.assertEqual(build_date_match.group(2), release_match.group(2))

    def test_openclaw_runtime_version_is_current_may_release(self) -> None:
        version_info = json.loads(Path("version.json").read_text(encoding="utf-8"))
        prepare_script = Path("scripts", "prepare-openclaw-runtime.ps1").read_text(
            encoding="utf-8"
        )

        default_match = re.search(
            r'\[string\]\$OpenClawVersion\s*=\s*"([^"]+)"',
            prepare_script,
        )

        self.assertIsNotNone(default_match)
        self.assertEqual("v2026.5.6", version_info["openclawVersion"])
        self.assertEqual("2026.5.6", default_match.group(1))


if __name__ == "__main__":
    unittest.main()
