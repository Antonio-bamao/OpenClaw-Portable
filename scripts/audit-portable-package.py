from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.services.portable_audit import audit_portable_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a portable OpenClaw package without modifying it.")
    parser.add_argument("--package-root", default=str(ROOT / "dist" / "OpenClaw-Portable"), help="Portable package root to audit.")
    parser.add_argument("--top", type=int, default=10, help="Number of largest directories to include.")
    parser.add_argument("--min-free-mb", type=float, default=500.0, help="Minimum recommended free space in MB.")
    parser.add_argument("--free-space-mb", type=float, default=None, help="Optional free space override in MB for tests or reports.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root)
    free_space_bytes = _resolve_free_space_bytes(package_root, args.free_space_mb)
    result = audit_portable_package(
        package_root,
        top_limit=args.top,
        free_space_bytes=free_space_bytes,
        min_free_space_bytes=int(args.min_free_mb * 1024 * 1024),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


def _resolve_free_space_bytes(package_root: Path, free_space_mb: float | None) -> int | None:
    if free_space_mb is not None:
        return int(free_space_mb * 1024 * 1024)
    if package_root.exists():
        return shutil.disk_usage(package_root).free
    return None


if __name__ == "__main__":
    raise SystemExit(main())
