import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from launcher.core.paths import PortablePaths
from launcher.services.runtime_mode import resolve_runtime_mode


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"runtime-mode-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class RuntimeModeTests(unittest.TestCase):
    def test_auto_uses_mock_when_portable_runtime_is_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")

            self.assertEqual(resolve_runtime_mode(paths), "mock")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_auto_uses_openclaw_when_portable_runtime_is_complete(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            (paths.runtime_dir / "openclaw").mkdir(parents=True, exist_ok=True)
            (paths.runtime_dir / "openclaw" / "openclaw.mjs").write_text("", encoding="utf-8")
            (paths.runtime_dir / "node").mkdir(parents=True, exist_ok=True)
            (paths.runtime_dir / "node" / "node.exe").write_text("", encoding="utf-8")

            self.assertEqual(resolve_runtime_mode(paths), "openclaw")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_explicit_mode_overrides_auto_detection(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")

            self.assertEqual(resolve_runtime_mode(paths, requested_mode="openclaw"), "openclaw")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_environment_mode_overrides_auto_detection(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")

            with patch.dict(os.environ, {"OPENCLAW_PORTABLE_RUNTIME_MODE": "openclaw"}):
                self.assertEqual(resolve_runtime_mode(paths), "openclaw")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
