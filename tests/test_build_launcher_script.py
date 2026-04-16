import unittest
from pathlib import Path


class BuildLauncherScriptTests(unittest.TestCase):
    def test_pyinstaller_includes_cffi_backend_for_pynacl(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("--hidden-import", content)
        self.assertIn("_cffi_backend", content)


if __name__ == "__main__":
    unittest.main()
