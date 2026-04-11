from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from launcher.services.update_signature import DEFAULT_UPDATE_SIGNING_KEY_ID, read_private_key_file, write_update_signature


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sign update-manifest.json for a portable package.")
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--private-key-path", type=Path, default=Path(".local") / "update-signing-private-key.txt")
    parser.add_argument("--key-id", default=DEFAULT_UPDATE_SIGNING_KEY_ID)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    private_key_b64 = read_private_key_file(args.private_key_path)
    write_update_signature(args.package_root, private_key_b64=private_key_b64, key_id=args.key_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
