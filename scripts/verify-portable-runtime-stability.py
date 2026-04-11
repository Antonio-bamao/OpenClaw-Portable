from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.services.runtime_stability import build_runtime_stability_verifier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repeated runtime stability verification against a portable package.")
    parser.add_argument("--package-root", required=True, help="Portable package root to verify.")
    parser.add_argument("--cold-runs", type=int, default=3, help="Number of isolated cold-start runs.")
    parser.add_argument("--restart-runs", type=int, default=2, help="Number of isolated restart runs.")
    parser.add_argument("--timeout-seconds", type=float, default=None, help="Optional per-run startup timeout override.")
    parser.add_argument("--output", default="", help="Optional JSON output file path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    verifier = build_runtime_stability_verifier()
    result = verifier.verify(
        package_root=Path(args.package_root),
        cold_runs=args.cold_runs,
        restart_runs=args.restart_runs,
        timeout_seconds=args.timeout_seconds,
    )
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
