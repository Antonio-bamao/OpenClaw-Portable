from __future__ import annotations

import json
import os
import subprocess
import time
import http.client
import urllib.error
import urllib.request
from pathlib import Path

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.core.port_resolver import PortResolver, PortResolution
from launcher.runtime.base import RuntimeAdapter, RuntimeHealth, RuntimeStatus


class MockRuntimeAdapter(RuntimeAdapter):
    def __init__(self, node_command: str = "node") -> None:
        self.node_command = node_command
        self._config: LauncherConfig | None = None
        self._paths: PortablePaths | None = None
        self._process: subprocess.Popen[str] | None = None
        self._port_resolution: PortResolution | None = None
        self._stdout_log: Path | None = None
        self._stderr_log: Path | None = None
        self._last_state = "idle"
        self._started_at_monotonic: float | None = None

    def prepare(self, config: LauncherConfig, paths: PortablePaths) -> None:
        paths.ensure_directories()
        self._config = config
        self._paths = paths
        self._port_resolution = PortResolver().resolve(config.bind_host, config.gateway_port)
        self._stdout_log = paths.logs_dir / "mock-runtime.out.log"
        self._stderr_log = paths.logs_dir / "mock-runtime.err.log"
        self._last_state = "ready"

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            return
        if not self._config or not self._paths or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before it can start")

        script_path = self._script_path()
        environment = {
            "OPENCLAW_BIND_HOST": self._config.bind_host,
            "OPENCLAW_PORT": str(self._port_resolution.port),
            "OPENCLAW_PROVIDER_NAME": self._config.provider_name,
            "OPENCLAW_MODEL": self._config.model,
            "OPENCLAW_OFFLINE_MODE": "1" if not self._read_api_key() else "0",
        }
        with self._stdout_log.open("w", encoding="utf-8") as stdout_file, self._stderr_log.open("w", encoding="utf-8") as stderr_file:
            self._process = subprocess.Popen(
                [self.node_command, str(script_path)],
                cwd=str(self._paths.project_root),
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                env={**os.environ, **environment},
            )
        self._wait_until_ready()
        self._last_state = "running"
        self._started_at_monotonic = time.monotonic()

    def stop(self) -> None:
        if not self._process:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None
        self._last_state = "stopped"
        self._started_at_monotonic = None

    def restart(self) -> None:
        self.stop()
        self.start()

    def status(self) -> RuntimeStatus:
        if not self._port_resolution:
            return RuntimeStatus(state="idle")
        if self._process and self._process.poll() is None:
            return RuntimeStatus(
                state="running",
                port=self._port_resolution.port,
                message=self._port_resolution.message,
                pid=self._process.pid,
                uptime_seconds=self._uptime_seconds(),
            )
        if self._process and self._process.poll() is not None:
            return RuntimeStatus(
                state="stopped",
                port=self._port_resolution.port,
                message=self._port_resolution.message,
                pid=self._process.pid,
            )
        return RuntimeStatus(state=self._last_state, port=self._port_resolution.port, message=self._port_resolution.message)

    def _uptime_seconds(self) -> int | None:
        if self._started_at_monotonic is None:
            return None
        return max(0, int(time.monotonic() - self._started_at_monotonic))

    def webui_url(self) -> str:
        if not self._config or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before URL can be resolved")
        return f"http://{self._config.bind_host}:{self._port_resolution.port}"

    def healthcheck(self) -> RuntimeHealth:
        try:
            with urllib.request.urlopen(f"{self.webui_url()}/health", timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return RuntimeHealth(ok=bool(payload.get("ok")), details=payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, http.client.HTTPException, OSError) as exc:
            return RuntimeHealth(ok=False, error=str(exc))

    def _script_path(self) -> Path:
        if not self._paths:
            raise RuntimeError("Runtime paths are not prepared")
        script_path = self._paths.runtime_dir / "mock-runtime" / "server.js"
        if not script_path.exists():
            raise FileNotFoundError(f"Mock runtime entrypoint not found: {script_path}")
        return script_path

    def _wait_until_ready(self) -> None:
        for _ in range(40):
            if self._process and self._process.poll() is not None:
                raise RuntimeError("Mock runtime exited before becoming healthy")
            health = self.healthcheck()
            if health.ok:
                return
            time.sleep(0.25)
        raise TimeoutError("Mock runtime did not become healthy in time")

    def _read_api_key(self) -> str:
        if not self._paths or not self._paths.env_file.exists():
            return ""
        for line in self._paths.env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENCLAW_API_KEY="):
                return line.split("=", 1)[1]
        return ""
