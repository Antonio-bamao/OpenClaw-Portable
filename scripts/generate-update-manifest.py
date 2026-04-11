from __future__ import annotations

import argparse
from pathlib import Path

from launcher.services.update_manifest import write_update_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate update-manifest.json for a portable package root.")
    parser.add_argument("--package-root", required=True, help="Portable package root directory")
    args = parser.parse_args()
    manifest_path = write_update_manifest(Path(args.package_root))
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
