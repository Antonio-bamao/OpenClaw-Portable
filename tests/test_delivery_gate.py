import json
import shutil
import subprocess
import unittest
import uuid
import zipfile
from pathlib import Path

from launcher.services.runtime_stability import RuntimeStabilityRun, RuntimeStabilityVerifier
from launcher.services.update_signature import generate_update_signing_keypair, write_update_signature

from launcher.services.delivery_gate import verify_delivery_flow


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"delivery-gate-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class FakeStabilityRunner:
    def run_cold_start(self, *, index: int, package_root: Path, runtime_mode: str, timeout_seconds: float | None) -> RuntimeStabilityRun:
        return RuntimeStabilityRun("cold_start", index, True, 1.5, 18789, True, "", "out.log", "err.log")

    def run_restart(self, *, index: int, package_root: Path, runtime_mode: str, timeout_seconds: float | None) -> RuntimeStabilityRun:
        return RuntimeStabilityRun("restart", index, True, 0.9, 18789, True, "", "out.log", "err.log")


class DeliveryGateTests(unittest.TestCase):
    def test_gate_passes_local_checks_and_marks_external_evidence_pending(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            release_dir = temp_dir / "release"
            self._write_minimal_package(package_root, version="v2026.04.3")
            release_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(release_dir / "OpenClaw-Portable-v2026.04.3.zip", "w") as archive:
                archive.writestr("OpenClaw-Portable/version.json", json.dumps({"version": "v2026.04.3"}))
                archive.writestr("OpenClaw-Portable/update-manifest.json", json.dumps({"manifestVersion": 1}))
                archive.writestr("OpenClaw-Portable/update-signature.json", json.dumps({"signature": "demo"}))
            write_file(
                release_dir / "update.json",
                json.dumps(
                    {
                        "version": "v2026.04.3",
                        "packageUrl": "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.3/OpenClaw-Portable-v2026.04.3.zip",
                    }
                ),
            )

            result = verify_delivery_flow(
                package_root=package_root,
                release_dir=release_dir,
                stability_verifier=RuntimeStabilityVerifier(FakeStabilityRunner()),
                cold_runs=1,
                restart_runs=1,
            )

            self.assertEqual(result.status, "pending")
            checks = {check.name: check for check in result.checks}
            self.assertEqual(checks["portable-package-audit"].status, "passed")
            self.assertEqual(checks["release-assets"].status, "passed")
            self.assertEqual(checks["runtime-stability"].status, "passed")
            self.assertEqual(checks["feishu-private-chat-e2e"].status, "pending")
            self.assertEqual(checks["removable-media-run"].status, "pending")
            self.assertEqual(checks["multi-engine-av-smartscreen"].status, "pending")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_gate_fails_when_release_assets_are_missing(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            release_dir = temp_dir / "release"
            self._write_minimal_package(package_root, version="v2026.04.3")

            result = verify_delivery_flow(package_root=package_root, release_dir=release_dir, cold_runs=0, restart_runs=0)

            self.assertEqual(result.status, "failed")
            checks = {check.name: check for check in result.checks}
            self.assertEqual(checks["release-assets"].status, "failed")
            self.assertIn("OpenClaw-Portable-v2026.04.3.zip", checks["release-assets"].message)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_gate_fails_when_release_zip_lacks_manifest_or_signature(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            release_dir = temp_dir / "release"
            self._write_minimal_package(package_root, version="v2026.04.3")
            release_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(release_dir / "OpenClaw-Portable-v2026.04.3.zip", "w") as archive:
                archive.writestr("OpenClaw-Portable/version.json", json.dumps({"version": "v2026.04.3"}))
            write_file(
                release_dir / "update.json",
                json.dumps(
                    {
                        "version": "v2026.04.3",
                        "packageUrl": "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.3/OpenClaw-Portable-v2026.04.3.zip",
                    }
                ),
            )

            result = verify_delivery_flow(package_root=package_root, release_dir=release_dir, cold_runs=0, restart_runs=0)

            checks = {check.name: check for check in result.checks}
            self.assertEqual(result.status, "failed")
            self.assertEqual(checks["release-assets"].status, "failed")
            self.assertIn("update-signature.json", checks["release-assets"].message)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_outputs_gate_json(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            release_dir = temp_dir / "release"
            self._write_minimal_package(package_root, version="v2026.04.3")

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "verify-delivery-flow.py"),
                    "--package-root",
                    str(package_root),
                    "--release-dir",
                    str(release_dir),
                    "--cold-runs",
                    "0",
                    "--restart-runs",
                    "0",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            document = json.loads(completed.stdout)
            self.assertEqual(document["status"], "failed")
            self.assertEqual(document["packageRoot"], str(package_root))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _write_minimal_package(self, package_root: Path, *, version: str) -> None:
        write_file(package_root / "OpenClawLauncher.exe", "exe")
        write_file(package_root / "version.json", json.dumps({"version": version}))
        write_file(package_root / "runtime" / "node" / "node.exe", "node")
        write_file(package_root / "runtime" / "openclaw" / "openclaw.mjs", "mjs")
        write_file(package_root / "runtime" / "openclaw" / "package.json", "{}")
        write_file(package_root / "runtime" / "openclaw" / "dist" / "entry.js", "entry")
        write_file(package_root / "assets" / "guide.html", "guide")
        write_file(package_root / "tools" / "export.bat", "tools")
        write_file(package_root / "state" / "provider-templates" / "qwen.json", "{}")
        write_file(package_root / "update-manifest.json", json.dumps({"manifestVersion": 1}))
        private_key_b64, _ = generate_update_signing_keypair()
        write_update_signature(package_root, private_key_b64=private_key_b64)


if __name__ == "__main__":
    unittest.main()
