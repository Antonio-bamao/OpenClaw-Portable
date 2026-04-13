from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.services.delivery_gate import FAILED, verify_delivery_flow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the local portable delivery flow without publishing anything.")
    parser.add_argument("--package-root", default=str(ROOT / "dist" / "OpenClaw-Portable"), help="Portable package root.")
    parser.add_argument("--release-dir", default=str(ROOT / "dist" / "release"), help="Release asset directory.")
    parser.add_argument("--cold-runs", type=int, default=0, help="Real runtime cold-start runs to include.")
    parser.add_argument("--restart-runs", type=int, default=0, help="Real runtime restart runs to include.")
    parser.add_argument("--runtime-mode", default="openclaw", choices=["openclaw", "mock"], help="Runtime mode for stability runs.")
    parser.add_argument("--timeout-seconds", type=float, default=None, help="Optional runtime startup timeout.")
    parser.add_argument("--feishu-e2e-evidence", default=None, help="Path to a real Feishu E2E evidence artifact.")
    parser.add_argument("--removable-media-path", default=None, help="Mounted U-disk or delivery-media path used for evidence.")
    parser.add_argument("--av-evidence", default=None, help="Path to multi-engine AV or SmartScreen evidence.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = verify_delivery_flow(
        package_root=Path(args.package_root),
        release_dir=Path(args.release_dir),
        cold_runs=args.cold_runs,
        restart_runs=args.restart_runs,
        runtime_mode=args.runtime_mode,
        timeout_seconds=args.timeout_seconds,
        feishu_e2e_evidence=Path(args.feishu_e2e_evidence) if args.feishu_e2e_evidence else None,
        removable_media_path=Path(args.removable_media_path) if args.removable_media_path else None,
        av_evidence=Path(args.av_evidence) if args.av_evidence else None,
    )
    document = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document + "\n", encoding="utf-8")
    print(document)
    return 1 if result.status == FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
