import unittest
from pathlib import Path


class BuildLauncherScriptTests(unittest.TestCase):
    def test_pyinstaller_includes_cffi_backend_for_pynacl(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("--hidden-import", content)
        self.assertIn("_cffi_backend", content)

    def test_build_scripts_check_native_command_exit_codes(self) -> None:
        for script in (Path("scripts") / "build-launcher.ps1", Path("scripts") / "build-release-assets.ps1"):
            with self.subTest(script=script):
                content = script.read_text(encoding="utf-8")

                self.assertIn("function Invoke-Native", content)
                self.assertIn("$LASTEXITCODE", content)
                self.assertIn("throw", content)
                self.assertNotIn("& $PythonExe @pyInstallerArgs", content)
                self.assertNotIn("& $PythonExe @command", content)

    def test_build_launcher_preserves_full_openclaw_runtime_manifest(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("Assert-OpenClawRuntimeManifest", content)
        self.assertIn('Join-Path $RuntimePath "dist\\\\plugins\\\\runtime\\\\index.js"', content)
        self.assertIn('"./plugin-sdk"', content)
        self.assertIn('"./cli-entry"', content)
        self.assertIn('runtime\\\\openclaw\\\\package.json', content)

    def test_build_launcher_prepares_openclaw_self_reference_before_manifest(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("ensure-openclaw-self-reference.py", content)
        self.assertLess(
            content.index("ensure-openclaw-self-reference.py"),
            content.index("generate-update-manifest.py"),
        )

    def test_build_launcher_installs_feishu_production_dependencies(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("$feishuPackageSpec = \"@openclaw/feishu@$openclawRuntimeVersion\"", content)
        self.assertNotIn('"@openclaw/feishu@latest"', content)
        self.assertIn('PSObject.Properties.Remove("devDependencies")', content)
        self.assertIn('Invoke-Native "npm" @("install", "--omit=dev", "--ignore-scripts", "--no-audit", "--no-fund")', content)
        self.assertLess(
            content.index('Invoke-Native "npm" @("install", "--omit=dev", "--ignore-scripts", "--no-audit", "--no-fund")'),
            content.index("prune-portable-runtime.py"),
        )

    def test_build_launcher_installs_qqbot_production_dependencies(self) -> None:
        script = Path("scripts") / "build-launcher.ps1"

        content = script.read_text(encoding="utf-8")

        self.assertIn("$qqbotPackageSpec = \"@openclaw/qqbot@$openclawRuntimeVersion\"", content)
        self.assertNotIn('"@openclaw/qqbot@latest"', content)
        self.assertIn('$qqbotExtDir = Join-Path $portableDist "runtime\\\\openclaw\\\\dist\\\\extensions\\\\qqbot"', content)
        self.assertLess(
            content.index("$qqbotPackageSpec"),
            content.index("prune-portable-runtime.py"),
        )


if __name__ == "__main__":
    unittest.main()
