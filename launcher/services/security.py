from __future__ import annotations

import base64
import ctypes
import getpass
import hashlib
import json
import os
import platform
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from nacl import exceptions, pwhash, secret, utils

from launcher.core.paths import PortablePaths


@dataclass(frozen=True)
class DeviceFingerprint:
    machine_id: str
    user_id: str
    display_name: str


class SecurityService:
    def __init__(self, paths: PortablePaths, fingerprint_provider=None) -> None:
        self.paths = paths
        self._fingerprint_provider = fingerprint_provider or current_device_fingerprint
        self._vault_key: bytes | None = None
        self.last_unlock_was_new_device = False

    def is_configured(self) -> bool:
        return self._security_file.exists() and self._vault_file.exists()

    def is_unlocked(self) -> bool:
        return self._vault_key is not None

    def setup(self, password: str, secrets: dict[str, str], *, trust_device: bool = True) -> None:
        normalized_password = password.strip()
        if not normalized_password:
            raise ValueError("管理密码不能为空。")
        self._ensure_security_dir()
        vault_key = utils.random(secret.SecretBox.KEY_SIZE)
        password_salt = utils.random(pwhash.argon2id.SALTBYTES)
        password_key = self._derive_password_key(normalized_password, password_salt)
        password_box = secret.SecretBox(password_key)
        wrapped_key = password_box.encrypt(vault_key)
        payload = {
            "version": 1,
            "passwordSalt": _b64encode(password_salt),
            "passwordWrappedKey": _b64encode(bytes(wrapped_key)),
            "passwordVerifier": _hash_key(password_key),
        }
        self._security_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._vault_key = vault_key
        self.save_secrets(secrets)
        if trust_device:
            self.trust_current_device()

    def unlock_with_trusted_device(self) -> bool:
        self.last_unlock_was_new_device = False
        device_key_path = self._device_key_file(self._current_device_hash())
        if not device_key_path.exists():
            return False
        payload = self._load_json_object(device_key_path)
        protected_key = _b64decode(str(payload.get("protectedKey") or ""))
        if not protected_key:
            return False
        try:
            vault_key = _dpapi_unprotect(protected_key)
        except OSError:
            return False
        if not self._can_open_vault(vault_key):
            return False
        self._vault_key = vault_key
        return True

    def requires_password_unlock(self) -> bool:
        return self.is_configured() and self._vault_key is None and not self.unlock_with_trusted_device()

    def unlock_with_password(self, password: str, *, trust_device: bool = True) -> bool:
        normalized_password = password.strip()
        security_payload = self._load_json_object(self._security_file)
        password_salt = _b64decode(str(security_payload.get("passwordSalt") or ""))
        wrapped_key = _b64decode(str(security_payload.get("passwordWrappedKey") or ""))
        verifier = str(security_payload.get("passwordVerifier") or "")
        if not normalized_password or not password_salt or not wrapped_key or not verifier:
            return False
        try:
            password_key = self._derive_password_key(normalized_password, password_salt)
            if not _constant_time_equal(_hash_key(password_key), verifier):
                return False
            vault_key = secret.SecretBox(password_key).decrypt(wrapped_key)
        except (exceptions.CryptoError, ValueError):
            return False
        if not self._can_open_vault(vault_key):
            return False
        self.last_unlock_was_new_device = not self._device_key_file(self._current_device_hash()).exists()
        self._vault_key = vault_key
        if trust_device:
            self.trust_current_device()
        return True

    def trust_current_device(self) -> None:
        if self._vault_key is None:
            raise RuntimeError("必须先解锁保险箱，才能信任当前设备。")
        self._ensure_security_dir()
        fingerprint = self._fingerprint_provider()
        payload = {
            "version": 1,
            "deviceHash": self._current_device_hash(),
            "displayName": fingerprint.display_name,
            "protectedKey": _b64encode(_dpapi_protect(self._vault_key)),
        }
        self._device_key_file(payload["deviceHash"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_secrets(self) -> dict[str, str]:
        if self._vault_key is None:
            raise RuntimeError("保险箱尚未解锁。")
        payload = self._load_json_object(self._vault_file)
        ciphertext = _b64decode(str(payload.get("ciphertext") or ""))
        if not ciphertext:
            return {}
        plaintext = secret.SecretBox(self._vault_key).decrypt(ciphertext)
        loaded = json.loads(plaintext.decode("utf-8"))
        if not isinstance(loaded, dict):
            return {}
        return {str(key): str(value) for key, value in loaded.items() if value is not None}

    def save_secrets(self, secrets: dict[str, str]) -> None:
        if self._vault_key is None:
            raise RuntimeError("保险箱尚未解锁。")
        self._ensure_security_dir()
        plaintext = json.dumps(secrets, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ciphertext = secret.SecretBox(self._vault_key).encrypt(plaintext)
        self._vault_file.write_text(
            json.dumps({"version": 1, "ciphertext": _b64encode(bytes(ciphertext))}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def _security_dir(self) -> Path:
        return self.paths.state_dir / "security"

    @property
    def _security_file(self) -> Path:
        return self._security_dir / "security.json"

    @property
    def _vault_file(self) -> Path:
        return self._security_dir / "vault.json"

    @property
    def _device_keys_dir(self) -> Path:
        return self._security_dir / "device-keys"

    def _ensure_security_dir(self) -> None:
        self.paths.ensure_directories()
        self._security_dir.mkdir(parents=True, exist_ok=True)
        self._device_keys_dir.mkdir(parents=True, exist_ok=True)

    def _device_key_file(self, device_hash: str) -> Path:
        return self._device_keys_dir / f"{device_hash}.json"

    def _current_device_hash(self) -> str:
        fingerprint = self._fingerprint_provider()
        text = f"{fingerprint.machine_id}\n{fingerprint.user_id}".encode("utf-8", errors="replace")
        return hashlib.sha256(text).hexdigest()

    def _derive_password_key(self, password: str, salt: bytes) -> bytes:
        return pwhash.argon2id.kdf(
            secret.SecretBox.KEY_SIZE,
            password.encode("utf-8"),
            salt,
            opslimit=pwhash.argon2id.OPSLIMIT_INTERACTIVE,
            memlimit=pwhash.argon2id.MEMLIMIT_INTERACTIVE,
        )

    def _can_open_vault(self, vault_key: bytes) -> bool:
        try:
            payload = self._load_json_object(self._vault_file)
            ciphertext = _b64decode(str(payload.get("ciphertext") or ""))
            if not ciphertext:
                return False
            secret.SecretBox(vault_key).decrypt(ciphertext)
            return True
        except (exceptions.CryptoError, ValueError, OSError, json.JSONDecodeError):
            return False

    def _load_json_object(self, path: Path) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload


def current_device_fingerprint() -> DeviceFingerprint:
    return DeviceFingerprint(
        machine_id=_windows_machine_guid() or str(uuid.getnode()),
        user_id=_windows_user_sid() or getpass.getuser(),
        display_name=f"{platform.node() or 'Windows PC'} / {getpass.getuser()}",
    )


def _windows_machine_guid() -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except OSError:
        return ""


def _windows_user_sid() -> str:
    if os.name != "nt":
        return ""
    try:
        import win32security  # type: ignore

        sid, _, _ = win32security.LookupAccountName(None, getpass.getuser())
        return win32security.ConvertSidToStringSid(sid)
    except Exception:
        return os.environ.get("USERNAME", "")


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    if not value:
        return b""
    return base64.b64decode(value.encode("ascii"))


def _hash_key(value: bytes) -> str:
    return hashlib.sha256(value + b":openclaw-security-verifier").hexdigest()


def _constant_time_equal(left: str, right: str) -> bool:
    return hashlib.sha256(left.encode()).digest() == hashlib.sha256(right.encode()).digest()


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi_protect(value: bytes) -> bytes:
    if os.name != "nt":
        return value
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_blob = _bytes_to_blob(value)
    out_blob = _DATA_BLOB()
    if not crypt32.CryptProtectData(ctypes.byref(in_blob), "OpenClaw Portable", None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(value: bytes) -> bytes:
    if os.name != "nt":
        return value
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_blob = _bytes_to_blob(value)
    out_blob = _DATA_BLOB()
    if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _bytes_to_blob(value: bytes) -> _DATA_BLOB:
    buffer = ctypes.create_string_buffer(value)
    blob = _DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    blob._buffer = buffer  # keep the buffer alive while the Windows API reads it
    return blob
