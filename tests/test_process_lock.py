import shutil
import unittest
import uuid
from pathlib import Path

from launcher.services.process_lock import SingleInstanceLock


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"process-lock-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class SingleInstanceLockTests(unittest.TestCase):
    def test_rejects_second_holder_until_first_releases(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            lock_path = temp_dir / "OpenClawLauncher.lock"
            first = SingleInstanceLock(lock_path)
            second = SingleInstanceLock(lock_path)

            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire())

            first.release()
            self.assertTrue(second.acquire())
            second.release()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
