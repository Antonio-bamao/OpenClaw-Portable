from __future__ import annotations

import shutil
import socket
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.runtime.base import RuntimeAdapter
from launcher.runtime.mock_runtime import MockRuntimeAdapter
from launcher.runtime.openclaw_runtime import OpenClawRuntimeAdapter


@dataclass(frozen=True)
class RuntimeStabilityRun:
    kind: str
    index: int
    ok: bool
    elapsed_seconds: float
    port: int | None
    health_ok: bool
    error: str
    stdout_log: str
    stderr_log: str

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "index": self.index,
            "ok": self.ok,
            "elapsedSeconds": round(self.elapsed_seconds, 2),
            "port": self.port,
            "healthOk": self.health_ok,
            "error": self.error,
            "stdoutLog": self.stdout_log,
            "stderrLog": self.stderr_log,
        }


@dataclass(frozen=True)
class RuntimeStabilitySummary:
    all_passed: bool
    cold_runs_passed: int
    restart_runs_passed: int
    max_elapsed_seconds: float
    avg_elapsed_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "allPassed": self.all_passed,
            "coldRunsPassed": self.cold_runs_passed,
            "restartRunsPassed": self.restart_runs_passed,
            "maxElapsedSeconds": round(self.max_elapsed_seconds, 2),
            "avgElapsedSeconds": round(self.avg_elapsed_seconds, 2),
        }


@dataclass(frozen=True)
class RuntimeStabilityResult:
    package_root: Path
    runtime_mode: str
    cold_runs_requested: int
    restart_runs_requested: int
    summary: RuntimeStabilitySummary
    runs: list[RuntimeStabilityRun]

    def to_dict(self) -> dict[str, object]:
        return {
            "packageRoot": str(self.package_root),
            "runtimeMode": self.runtime_mode,
            "coldRunsRequested": self.cold_runs_requested,
            "restartRunsRequested": self.restart_runs_requested,
            "summary": self.summary.to_dict(),
            "runs": [run.to_dict() for run in self.runs],
        }


def build_runtime_stability_result(
    *,
    package_root: Path,
    runtime_mode: str,
    cold_runs_requested: int,
    restart_runs_requested: int,
    runs: list[RuntimeStabilityRun],
) -> RuntimeStabilityResult:
    elapsed_values = [run.elapsed_seconds for run in runs]
    summary = RuntimeStabilitySummary(
        all_passed=all(run.ok for run in runs) if runs else True,
        cold_runs_passed=sum(1 for run in runs if run.kind == "cold_start" and run.ok),
        restart_runs_passed=sum(1 for run in runs if run.kind == "restart" and run.ok),
        max_elapsed_seconds=max(elapsed_values, default=0.0),
        avg_elapsed_seconds=(sum(elapsed_values) / len(elapsed_values)) if elapsed_values else 0.0,
    )
    return RuntimeStabilityResult(
        package_root=package_root,
        runtime_mode=runtime_mode,
        cold_runs_requested=cold_runs_requested,
        restart_runs_requested=restart_runs_requested,
        summary=summary,
        runs=runs,
    )


class RuntimeVerificationPathsFactory:
    def __init__(self, base_temp_root: Path | None = None) -> None:
        self._base_temp_root = base_temp_root

    def create(self, *, package_root: Path, run_label: str) -> PortablePaths:
        base_root = self._base_temp_root or (Path(tempfile.gettempdir()) / "OpenClawPortableVerification")
        isolated_root = base_root / run_label
        state_root = isolated_root / "state"
        temp_base = isolated_root / "system-temp"
        temp_root = temp_base / "OpenClawPortable"
        return PortablePaths(
            project_root=package_root,
            runtime_dir=package_root / "runtime",
            state_dir=state_root,
            assets_dir=package_root / "assets",
            tools_dir=package_root / "tools",
            temp_root=temp_root,
            logs_dir=temp_root / "logs",
            cache_dir=temp_root / "cache",
            config_file=state_root / "openclaw.json",
            runtime_config_file=state_root / "runtime" / "openclaw.json",
            env_file=state_root / ".env",
            provider_templates_dir=state_root / "provider-templates",
            workspace_dir=state_root / "workspace",
        )


class RealRuntimeStabilityRunner:
    def __init__(self, *, node_command: str = "node", paths_factory: RuntimeVerificationPathsFactory | None = None) -> None:
        self._node_command = node_command
        self._paths_factory = paths_factory or RuntimeVerificationPathsFactory()

    def run_cold_start(
        self,
        *,
        index: int,
        package_root: Path,
        runtime_mode: str,
        timeout_seconds: float | None,
    ) -> RuntimeStabilityRun:
        run_label = f"cold-{index}-{int(time.time() * 1000)}"
        paths = self._paths_factory.create(package_root=package_root, run_label=run_label)
        self._stage_verification_state(package_root=package_root, paths=paths)
        runtime_adapter = self._build_runtime_adapter(paths=paths, runtime_mode=runtime_mode, timeout_seconds=timeout_seconds)
        return self._execute_run(
            kind="cold_start",
            index=index,
            runtime_adapter=runtime_adapter,
            runtime_mode=runtime_mode,
            paths=paths,
            restart=False,
        )

    def run_restart(
        self,
        *,
        index: int,
        package_root: Path,
        runtime_mode: str,
        timeout_seconds: float | None,
    ) -> RuntimeStabilityRun:
        run_label = f"restart-{index}-{int(time.time() * 1000)}"
        paths = self._paths_factory.create(package_root=package_root, run_label=run_label)
        self._stage_verification_state(package_root=package_root, paths=paths)
        runtime_adapter = self._build_runtime_adapter(paths=paths, runtime_mode=runtime_mode, timeout_seconds=timeout_seconds)
        return self._execute_run(
            kind="restart",
            index=index,
            runtime_adapter=runtime_adapter,
            runtime_mode=runtime_mode,
            paths=paths,
            restart=True,
        )

    def _stage_verification_state(self, *, package_root: Path, paths: PortablePaths) -> None:
        if paths.state_dir.exists():
            shutil.rmtree(paths.state_dir, ignore_errors=True)
        if paths.temp_root.parent.exists():
            shutil.rmtree(paths.temp_root.parent, ignore_errors=True)
        paths.ensure_directories()
        source_templates = package_root / "state" / "provider-templates"
        if source_templates.exists():
            shutil.copytree(source_templates, paths.provider_templates_dir, dirs_exist_ok=True)
        source_config = package_root / "state" / "openclaw.json"
        if source_config.exists():
            shutil.copy2(source_config, paths.runtime_config_file)
        source_env = package_root / "state" / ".env"
        if source_env.exists():
            shutil.copy2(source_env, paths.env_file)

    def _build_runtime_adapter(self, *, paths: PortablePaths, runtime_mode: str, timeout_seconds: float | None) -> RuntimeAdapter:
        runtime_adapter: RuntimeAdapter
        if runtime_mode == "openclaw" and timeout_seconds is not None:
            runtime_adapter = OpenClawRuntimeAdapter(node_command=self._node_command, startup_timeout_seconds=timeout_seconds)
        elif runtime_mode == "mock":
            runtime_adapter = MockRuntimeAdapter(node_command=self._node_command)
        elif runtime_mode == "openclaw":
            runtime_adapter = OpenClawRuntimeAdapter(node_command=self._node_command)
        else:
            raise ValueError(f"Unsupported runtime mode for verification: {runtime_mode}")
        runtime_adapter.prepare(_default_launcher_config(), paths)
        return runtime_adapter

    def _execute_run(
        self,
        *,
        kind: str,
        index: int,
        runtime_adapter: RuntimeAdapter,
        runtime_mode: str,
        paths: PortablePaths,
        restart: bool,
    ) -> RuntimeStabilityRun:
        error = ""
        elapsed_seconds = 0.0
        try:
            if restart:
                runtime_adapter.start()
            start_time = time.monotonic()
            if restart:
                runtime_adapter.restart()
            else:
                runtime_adapter.start()
            elapsed_seconds = time.monotonic() - start_time
            status = runtime_adapter.status()
            health = runtime_adapter.healthcheck()
            return RuntimeStabilityRun(
                kind=kind,
                index=index,
                ok=health.ok,
                elapsed_seconds=elapsed_seconds,
                port=status.port,
                health_ok=health.ok,
                error=health.error or "",
                stdout_log=str(_stdout_log_path(paths, runtime_mode)),
                stderr_log=str(_stderr_log_path(paths, runtime_mode)),
            )
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            status = runtime_adapter.status()
            return RuntimeStabilityRun(
                kind=kind,
                index=index,
                ok=False,
                elapsed_seconds=elapsed_seconds,
                port=status.port,
                health_ok=False,
                error=error,
                stdout_log=str(_stdout_log_path(paths, runtime_mode)),
                stderr_log=str(_stderr_log_path(paths, runtime_mode)),
            )
        finally:
            runtime_adapter.stop()


class RuntimeStabilityVerifier:
    def __init__(self, runner) -> None:
        self._runner = runner

    def verify(
        self,
        *,
        package_root: Path,
        cold_runs: int,
        restart_runs: int,
        runtime_mode: str = "openclaw",
        timeout_seconds: float | None = None,
    ) -> RuntimeStabilityResult:
        package_root = package_root.resolve()
        if not package_root.exists():
            raise FileNotFoundError(f"Portable package root does not exist: {package_root}")
        if not package_root.is_dir():
            raise NotADirectoryError(f"Portable package root is not a directory: {package_root}")
        runs: list[RuntimeStabilityRun] = []
        for index in range(1, cold_runs + 1):
            runs.append(
                self._runner.run_cold_start(
                    index=index,
                    package_root=package_root,
                    runtime_mode=runtime_mode,
                    timeout_seconds=timeout_seconds,
                )
            )
        for index in range(1, restart_runs + 1):
            runs.append(
                self._runner.run_restart(
                    index=index,
                    package_root=package_root,
                    runtime_mode=runtime_mode,
                    timeout_seconds=timeout_seconds,
                )
            )
        return build_runtime_stability_result(
            package_root=package_root,
            runtime_mode=runtime_mode,
            cold_runs_requested=cold_runs,
            restart_runs_requested=restart_runs,
            runs=runs,
        )


def build_runtime_stability_verifier(node_command: str = "node") -> RuntimeStabilityVerifier:
    return RuntimeStabilityVerifier(runner=RealRuntimeStabilityRunner(node_command=node_command))


def _default_launcher_config() -> LauncherConfig:
    return LauncherConfig(
        admin_password="portable-demo-pass",
        provider_id="dashscope",
        provider_name="通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        gateway_port=_reserve_free_port(),
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


def _reserve_free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def _stdout_log_path(paths: PortablePaths, runtime_mode: str) -> Path:
    return paths.logs_dir / ("openclaw-runtime.out.log" if runtime_mode == "openclaw" else "mock-runtime.out.log")


def _stderr_log_path(paths: PortablePaths, runtime_mode: str) -> Path:
    return paths.logs_dir / ("openclaw-runtime.err.log" if runtime_mode == "openclaw" else "mock-runtime.err.log")
