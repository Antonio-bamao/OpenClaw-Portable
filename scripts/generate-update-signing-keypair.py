from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from launcher.services.update_signature import DEFAULT_UPDATE_SIGNING_KEY_ID, generate_update_signing_keypair


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an Ed25519 keypair for update-package signing.")
    parser.add_argument("--private-key-path", type=Path, default=Path(".local") / "update-signing-private-key.txt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    private_key_b64, public_key_b64 = generate_update_signing_keypair()
    args.private_key_path.parent.mkdir(parents=True, exist_ok=True)
    args.private_key_path.write_text(private_key_b64 + "\n", encoding="utf-8")
    print(f"keyId={DEFAULT_UPDATE_SIGNING_KEY_ID}")
    print(f"publicKey={public_key_b64}")
    print(f"privateKeyPath={args.private_key_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
