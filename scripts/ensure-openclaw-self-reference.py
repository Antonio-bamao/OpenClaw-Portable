from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare node_modules/openclaw for bundled external plugins.")
    parser.add_argument("--runtime-path", required=True, help="Path to the OpenClaw runtime root.")
    args = parser.parse_args()

    runtime_path = Path(args.runtime_path).resolve()
    OpenClawRuntimeAdapter()._ensure_openclaw_self_reference(runtime_path)
    print(runtime_path / "node_modules" / "openclaw")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
