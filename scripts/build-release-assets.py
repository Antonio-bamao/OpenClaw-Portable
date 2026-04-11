from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from launcher.services.release_assets import DEFAULT_RELEASE_REPOSITORY, build_release_assets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build GitHub Releases assets for the portable package.")
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository", default=DEFAULT_RELEASE_REPOSITORY)
    parser.add_argument("--note", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_release_assets(
        package_root=args.package_root,
        output_dir=args.output_dir,
        repository=args.repository,
        notes=args.note,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
