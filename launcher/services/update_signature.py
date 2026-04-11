from __future__ import annotations

import base64
import json
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


DEFAULT_UPDATE_SIGNING_KEY_ID = "portable-ed25519-v1"
DEFAULT_UPDATE_SIGNING_PUBLIC_KEY = "WN6EsYlyLFiOcSLnSlzqJfch9qTtiyscl7Og1lgk6M0="


def generate_update_signing_keypair() -> tuple[str, str]:
    signing_key = SigningKey.generate()
    return (
        base64.b64encode(bytes(signing_key)).decode("ascii"),
        base64.b64encode(bytes(signing_key.verify_key)).decode("ascii"),
    )


def build_update_signature_document(
    *,
    manifest_bytes: bytes,
    private_key_b64: str,
    key_id: str = DEFAULT_UPDATE_SIGNING_KEY_ID,
) -> dict[str, str]:
    signing_key = SigningKey(_decode_base64_value(private_key_b64, label="更新私钥"))
    signature = signing_key.sign(manifest_bytes).signature
    return {
        "algorithm": "Ed25519",
        "keyId": key_id,
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def write_update_signature(
    package_root: Path,
    *,
    private_key_b64: str,
    key_id: str = DEFAULT_UPDATE_SIGNING_KEY_ID,
) -> Path:
    package_root = package_root.resolve()
    manifest_path = package_root / "update-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("更新包缺少 update-manifest.json，无法生成数字签名。")
    signature_document = build_update_signature_document(
        manifest_bytes=manifest_path.read_bytes(),
        private_key_b64=private_key_b64,
        key_id=key_id,
    )
    signature_path = package_root / "update-signature.json"
    signature_path.write_text(json.dumps(signature_document, ensure_ascii=True, indent=2), encoding="utf-8")
    return signature_path


def verify_update_signature(
    package_root: Path,
    *,
    expected_key_id: str = DEFAULT_UPDATE_SIGNING_KEY_ID,
    public_key_b64: str = DEFAULT_UPDATE_SIGNING_PUBLIC_KEY,
) -> None:
    package_root = package_root.resolve()
    manifest_path = package_root / "update-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("更新包缺少 update-manifest.json。")
    signature_path = package_root / "update-signature.json"
    if not signature_path.exists():
        raise FileNotFoundError("更新包缺少 update-signature.json。")
    try:
        signature_document = json.loads(signature_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("更新包的数字签名文件不是合法 JSON。") from exc
    verify_update_signature_document(
        manifest_bytes=manifest_path.read_bytes(),
        signature_document=signature_document,
        expected_key_id=expected_key_id,
        public_key_b64=public_key_b64,
    )


def verify_update_signature_document(
    *,
    manifest_bytes: bytes,
    signature_document: dict[str, object],
    expected_key_id: str,
    public_key_b64: str,
) -> None:
    algorithm = str(signature_document.get("algorithm") or "").strip()
    if algorithm != "Ed25519":
        raise ValueError("更新包的数字签名算法不受支持。")
    key_id = str(signature_document.get("keyId") or "").strip()
    if key_id != expected_key_id:
        raise ValueError("更新包签名 keyId 不匹配。")
    signature_b64 = str(signature_document.get("signature") or "").strip()
    if not signature_b64:
        raise ValueError("更新包缺少有效的数字签名。")

    public_key = VerifyKey(_decode_base64_value(public_key_b64, label="更新公钥"))
    signature = _decode_base64_value(signature_b64, label="更新签名")
    try:
        public_key.verify(manifest_bytes, signature)
    except BadSignatureError as exc:
        raise ValueError("更新包数字签名校验失败。") from exc


def read_private_key_file(private_key_path: Path) -> str:
    if not private_key_path.exists():
        raise FileNotFoundError(f"更新签名私钥不存在：{private_key_path}")
    return private_key_path.read_text(encoding="utf-8").strip()


def _decode_base64_value(value: str, *, label: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{label} 不是合法的 base64。") from exc
