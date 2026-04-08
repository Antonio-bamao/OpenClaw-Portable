from __future__ import annotations

import os

from launcher.core.paths import PortablePaths


SUPPORTED_RUNTIME_MODES = {"mock", "openclaw"}


def resolve_runtime_mode(paths: PortablePaths, requested_mode: str | None = None) -> str:
    mode = requested_mode or os.environ.get("OPENCLAW_PORTABLE_RUNTIME_MODE")
    if mode:
        if mode not in SUPPORTED_RUNTIME_MODES:
            raise ValueError(f"Unsupported runtime mode: {mode}")
        return mode

    if _has_complete_portable_openclaw_runtime(paths):
        return "openclaw"
    return "mock"


def _has_complete_portable_openclaw_runtime(paths: PortablePaths) -> bool:
    return (paths.runtime_dir / "openclaw" / "openclaw.mjs").exists() and (paths.runtime_dir / "node" / "node.exe").exists()
