from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.services.wechat_plugin_smoke import (
    run_wechat_plugin_gateway_smoke,
    verify_wechat_plugin_smoke_prerequisites,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a packaged OpenClaw runtime can register an installed WeChat npm plugin.")
    parser.add_argument("--package-root", default=str(ROOT / "dist" / "OpenClaw-Portable"), help="Portable package root with installed WeChat plugin state.")
    parser.add_argument("--timeout-seconds", type=float, default=45.0, help="Gateway startup timeout.")
    parser.add_argument("--post-ready-wait-seconds", type=float, default=3.0, help="Extra stderr scan window after HTTP readiness.")
    parser.add_argument("--prerequisites-only", action="store_true", help="Only check package/plugin files; do not start gateway.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root)
    if args.prerequisites_only:
        missing = verify_wechat_plugin_smoke_prerequisites(package_root.resolve())
        document = {
            "ok": not missing,
            "packageRoot": str(package_root.resolve()),
            "missing": missing,
        }
    else:
        result = run_wechat_plugin_gateway_smoke(
            package_root,
            timeout_seconds=args.timeout_seconds,
            post_ready_wait_seconds=args.post_ready_wait_seconds,
        )
        document = result.to_dict()
    payload = json.dumps(document, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if document.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
