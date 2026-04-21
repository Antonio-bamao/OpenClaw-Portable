import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from launcher.services.runtime_stability import (
    RealRuntimeStabilityRunner,
    RuntimeStabilityRun,
    RuntimeStabilityVerifier,
    RuntimeVerificationPathsFactory,
    build_runtime_stability_result,
)


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"runtime-stability-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class FakeRunner:
    def __init__(self, *, cold_runs: list[RuntimeStabilityRun], restart_runs: list[RuntimeStabilityRun]) -> None:
        self._cold_runs = list(cold_runs)
        self._restart_runs = list(restart_runs)
        self.calls: list[tuple[str, int, Path, str, float | None]] = []

    def run_cold_start(self, *, index: int, package_root: Path, runtime_mode: str, timeout_seconds: float | None) -> RuntimeStabilityRun:
        self.calls.append(("cold_start", index, package_root, runtime_mode, timeout_seconds))
        return self._cold_runs[index - 1]

    def run_restart(self, *, index: int, package_root: Path, runtime_mode: str, timeout_seconds: float | None) -> RuntimeStabilityRun:
        self.calls.append(("restart", index, package_root, runtime_mode, timeout_seconds))
        return self._restart_runs[index - 1]


class RuntimeStabilityTests(unittest.TestCase):
    def test_verifier_summarizes_cold_and_restart_runs(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            runner = FakeRunner(
                cold_runs=[
                    RuntimeStabilityRun("cold_start", 1, True, 31.2, 18789, True, "", "out-1.log", "err-1.log"),
                    RuntimeStabilityRun("cold_start", 2, True, 28.4, 18790, True, "", "out-2.log", "err-2.log"),
                ],
                restart_runs=[
                    RuntimeStabilityRun("restart", 1, True, 12.1, 18790, True, "", "out-r1.log", "err-r1.log"),
                ],
            )
            verifier = RuntimeStabilityVerifier(runner=runner)

            result = verifier.verify(package_root=package_root, cold_runs=2, restart_runs=1)

            self.assertTrue(result.summary.all_passed)
            self.assertEqual(result.summary.cold_runs_passed, 2)
            self.assertEqual(result.summary.restart_runs_passed, 1)
            self.assertAlmostEqual(result.summary.max_elapsed_seconds, 31.2)
            self.assertAlmostEqual(result.summary.avg_elapsed_seconds, (31.2 + 28.4 + 12.1) / 3)
            self.assertEqual(len(result.runs), 3)
            self.assertEqual(
                runner.calls,
                [
                    ("cold_start", 1, package_root, "openclaw", None),
                    ("cold_start", 2, package_root, "openclaw", None),
                    ("restart", 1, package_root, "openclaw", None),
                ],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_verifier_normalizes_package_root_before_runner_calls(self) -> None:
        temp_dir = make_workspace_temp_dir()
        previous_cwd = Path.cwd()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            runner = FakeRunner(
                cold_runs=[
                    RuntimeStabilityRun("cold_start", 1, True, 1.0, 18789, True, "", "out.log", "err.log"),
                ],
                restart_runs=[],
            )
            verifier = RuntimeStabilityVerifier(runner=runner)

            import os

            os.chdir(temp_dir)
            verifier.verify(package_root=Path("OpenClaw-Portable"), cold_runs=1, restart_runs=0)

            self.assertEqual(runner.calls[0][2], package_root.resolve())
        finally:
            import os

            os.chdir(previous_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_failed_run_keeps_error_and_log_paths(self) -> None:
        result = build_runtime_stability_result(
            package_root=Path("demo"),
            runtime_mode="openclaw",
            cold_runs_requested=1,
            restart_runs_requested=0,
            runs=[
                RuntimeStabilityRun(
                    kind="cold_start",
                    index=1,
                    ok=False,
                    elapsed_seconds=90.0,
                    port=None,
                    health_ok=False,
                    error="runtime did not become healthy in time",
                    stdout_log="C:/tmp/out.log",
                    stderr_log="C:/tmp/err.log",
                )
            ],
        )

        document = result.to_dict()

        self.assertFalse(document["summary"]["allPassed"])
        self.assertEqual(document["runs"][0]["error"], "runtime did not become healthy in time")
        self.assertEqual(document["runs"][0]["stderrLog"], "C:/tmp/err.log")
        self.assertEqual(document["runs"][0]["elapsedSeconds"], 90.0)

    def test_runner_uses_isolated_temp_state_roots(self) -> None:
        package_root = Path("C:/repo/dist/OpenClaw-Portable")
        factory = RuntimeVerificationPathsFactory(base_temp_root=Path("C:/tmp/checks"))

        created = factory.create(package_root=package_root, run_label="cold-1")

        self.assertEqual(created.project_root, package_root)
        self.assertEqual(created.runtime_dir, package_root / "runtime")
        self.assertNotEqual(created.state_dir, package_root / "state")
        self.assertIn("checks", str(created.state_dir))
        self.assertEqual(created.provider_templates_dir.parent, created.state_dir)
        self.assertEqual(created.temp_root.parent.name, "system-temp")

    def test_cli_outputs_json_report(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "verify-portable-runtime-stability.py"),
                    "--package-root",
                    str(package_root),
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

            self.assertEqual(completed.returncode, 0, completed.stderr)
            document = json.loads(completed.stdout)
            self.assertEqual(document["packageRoot"], str(package_root))
            self.assertEqual(document["coldRunsRequested"], 0)
            self.assertEqual(document["restartRunsRequested"], 0)
            self.assertEqual(document["runs"], [])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_stage_verification_state_copies_only_provider_templates_into_isolated_state(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            (package_root / "state" / "provider-templates" / "qwen.json").parent.mkdir(parents=True, exist_ok=True)
            (package_root / "state" / "provider-templates" / "qwen.json").write_text("{}", encoding="utf-8")

            factory = RuntimeVerificationPathsFactory(base_temp_root=temp_dir / "verification")
            runner = RealRuntimeStabilityRunner(paths_factory=factory)
            paths = factory.create(package_root=package_root, run_label="cold-1")

            runner._stage_verification_state(package_root=package_root, paths=paths)

            self.assertTrue((paths.provider_templates_dir / "qwen.json").exists())
            self.assertFalse((paths.state_dir / "openclaw.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_stage_verification_state_preserves_runtime_config_and_env_without_launcher_schema(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            package_root.mkdir(parents=True, exist_ok=True)
            expected_config = json.dumps(
                {
                    "gateway": {
                        "auth": {
                            "mode": "token",
                            "token": "demo-token",
                        }
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            (package_root / "state").mkdir(parents=True, exist_ok=True)
            (package_root / "state" / "openclaw.json").write_text(expected_config, encoding="utf-8")
            (package_root / "state" / ".env").write_text("OPENCLAW_API_KEY=sk-demo\n", encoding="utf-8")

            factory = RuntimeVerificationPathsFactory(base_temp_root=temp_dir / "verification")
            runner = RealRuntimeStabilityRunner(paths_factory=factory)
            paths = factory.create(package_root=package_root, run_label="cold-1")

            runner._stage_verification_state(package_root=package_root, paths=paths)

            self.assertEqual(paths.runtime_config_file.read_text(encoding="utf-8"), expected_config)
            self.assertEqual(paths.env_file.read_text(encoding="utf-8"), "OPENCLAW_API_KEY=sk-demo\n")
            self.assertNotIn("provider_id", paths.runtime_config_file.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
