import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.services.update_signature import (
    DEFAULT_UPDATE_SIGNING_KEY_ID,
    build_update_signature_document,
    generate_update_signing_keypair,
    verify_update_signature,
    verify_update_signature_document,
    write_update_signature,
)


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"update-signature-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class UpdateSignatureTests(unittest.TestCase):
    def test_generate_keypair_returns_base64_private_and_public_keys(self) -> None:
        private_key, public_key = generate_update_signing_keypair()
        self.assertTrue(private_key)
        self.assertTrue(public_key)

    def test_sign_and_verify_manifest_bytes_round_trip(self) -> None:
        private_key, public_key = generate_update_signing_keypair()
        signature_document = build_update_signature_document(
            manifest_bytes=b"{}",
            private_key_b64=private_key,
        )

        verify_update_signature_document(
            manifest_bytes=b"{}",
            signature_document=signature_document,
            expected_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
            public_key_b64=public_key,
        )

    def test_verify_signature_document_rejects_tampered_manifest_bytes(self) -> None:
        private_key, public_key = generate_update_signing_keypair()
        signature_document = build_update_signature_document(
            manifest_bytes=b'{"a":1}',
            private_key_b64=private_key,
        )

        with self.assertRaisesRegex(ValueError, "数字签名校验失败"):
            verify_update_signature_document(
                manifest_bytes=b'{"a":2}',
                signature_document=signature_document,
                expected_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
                public_key_b64=public_key,
            )

    def test_verify_signature_document_rejects_mismatched_key_id(self) -> None:
        private_key, public_key = generate_update_signing_keypair()
        signature_document = build_update_signature_document(
            manifest_bytes=b"{}",
            private_key_b64=private_key,
        )

        with self.assertRaisesRegex(ValueError, "keyId"):
            verify_update_signature_document(
                manifest_bytes=b"{}",
                signature_document=signature_document,
                expected_key_id="different-key",
                public_key_b64=public_key,
            )

    def test_verify_signature_document_accepts_secondary_trusted_key_id(self) -> None:
        _, old_public_key = generate_update_signing_keypair()
        new_private_key, new_public_key = generate_update_signing_keypair()
        signature_document = build_update_signature_document(
            manifest_bytes=b"{}",
            private_key_b64=new_private_key,
            key_id="portable-ed25519-v2",
        )

        verify_update_signature_document(
            manifest_bytes=b"{}",
            signature_document=signature_document,
            trusted_public_keys={
                DEFAULT_UPDATE_SIGNING_KEY_ID: old_public_key,
                "portable-ed25519-v2": new_public_key,
            },
        )

    def test_verify_signature_document_rejects_untrusted_key_id(self) -> None:
        private_key, _ = generate_update_signing_keypair()
        _, trusted_public_key = generate_update_signing_keypair()
        signature_document = build_update_signature_document(
            manifest_bytes=b"{}",
            private_key_b64=private_key,
            key_id="portable-ed25519-unknown",
        )

        with self.assertRaisesRegex(ValueError, "keyId"):
            verify_update_signature_document(
                manifest_bytes=b"{}",
                signature_document=signature_document,
                trusted_public_keys={
                    DEFAULT_UPDATE_SIGNING_KEY_ID: trusted_public_key,
                },
            )

    def test_write_and_verify_signature_file_for_package_root(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            manifest_path = package_root / "update-manifest.json"
            manifest_path.write_text(json.dumps({"manifestVersion": 1}, ensure_ascii=True, indent=2), encoding="utf-8")
            private_key, public_key = generate_update_signing_keypair()

            signature_path = write_update_signature(package_root, private_key_b64=private_key)

            self.assertTrue(signature_path.exists())
            verify_update_signature(
                package_root,
                expected_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
                public_key_b64=public_key,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
