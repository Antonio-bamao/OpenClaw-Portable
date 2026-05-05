import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.paths import PortablePaths
from launcher.services.security import DeviceFingerprint, SecurityService


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"security-test-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class SecurityServiceTests(unittest.TestCase):
    def test_setup_encrypts_vault_and_trusts_current_device(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            service = SecurityService(paths, fingerprint_provider=lambda: DeviceFingerprint("machine-a", "user-a", "PC-A"))

            service.setup("demo-pass", {"model.apiKey": "sk-demo"})

            self.assertTrue(service.is_configured())
            self.assertTrue(service.unlock_with_trusted_device())
            self.assertEqual(service.load_secrets()["model.apiKey"], "sk-demo")
            self.assertNotIn("sk-demo", (paths.state_dir / "security" / "vault.json").read_text(encoding="utf-8"))
            self.assertNotIn("demo-pass", (paths.state_dir / "security" / "security.json").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_new_device_requires_password_then_can_be_trusted(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            first_device = lambda: DeviceFingerprint("machine-a", "user-a", "PC-A")
            second_device = lambda: DeviceFingerprint("machine-b", "user-b", "PC-B")

            SecurityService(paths, fingerprint_provider=first_device).setup("demo-pass", {"model.apiKey": "sk-demo"})
            moved_service = SecurityService(paths, fingerprint_provider=second_device)

            self.assertFalse(moved_service.unlock_with_trusted_device())
            self.assertTrue(moved_service.requires_password_unlock())
            self.assertFalse(moved_service.unlock_with_password("wrong-pass"))
            self.assertTrue(moved_service.unlock_with_password("demo-pass", trust_device=True))
            self.assertTrue(moved_service.last_unlock_was_new_device)
            self.assertEqual(moved_service.load_secrets()["model.apiKey"], "sk-demo")

            reopened_service = SecurityService(paths, fingerprint_provider=second_device)
            self.assertTrue(reopened_service.unlock_with_trusted_device())
            self.assertFalse(reopened_service.last_unlock_was_new_device)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_password_unlock_without_trusting_device_is_session_only(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")
            SecurityService(paths, fingerprint_provider=lambda: DeviceFingerprint("machine-a", "user-a", "PC-A")).setup(
                "demo-pass",
                {"model.apiKey": "sk-demo"},
            )
            moved_service = SecurityService(paths, fingerprint_provider=lambda: DeviceFingerprint("machine-b", "user-b", "PC-B"))

            self.assertTrue(moved_service.unlock_with_password("demo-pass", trust_device=False))
            self.assertEqual(moved_service.load_secrets()["model.apiKey"], "sk-demo")
            self.assertFalse(SecurityService(paths, fingerprint_provider=lambda: DeviceFingerprint("machine-b", "user-b", "PC-B")).unlock_with_trusted_device())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
