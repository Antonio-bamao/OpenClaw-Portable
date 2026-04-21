from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.core.paths import PortablePaths
from launcher.services.feishu_probe import verify_feishu_channel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the local Feishu channel probe and emit evidence JSON.")
    parser.add_argument("--project-root", default=str(ROOT), help="Portable package or repo root that contains state/runtime.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="Timeout for `channels status --probe --json`.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_root = Path(args.project_root).resolve()
    document: dict[str, object]
    exit_code = 1

    try:
        evidence = verify_feishu_channel(
            PortablePaths.for_root(project_root),
            timeout_seconds=max(args.timeout_seconds, 1),
        )
        document = {
            "status": "passed" if evidence.ok else "failed",
            "projectRoot": str(project_root),
            "message": "Feishu live probe passed." if evidence.ok else (evidence.last_error or "Feishu live probe failed."),
            "evidence": evidence.to_dict(),
        }
        exit_code = 0 if evidence.ok else 1
    except Exception as exc:  # noqa: BLE001
        document = {
            "status": "failed",
            "projectRoot": str(project_root),
            "message": str(exc),
        }

    rendered = json.dumps(document, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
