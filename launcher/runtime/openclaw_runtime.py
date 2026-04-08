from __future__ import annotations

import os
import subprocess
import time
import socket
from pathlib import Path

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.core.port_resolver import PortResolver, PortResolution
from launcher.runtime.base import RuntimeAdapter, RuntimeHealth, RuntimeStatus


class OpenClawRuntimeAdapter(RuntimeAdapter):
    def __init__(self, node_command: str = "node", startup_timeout_seconds: float = 60) -> None:
        self.node_command = node_command
        self.startup_timeout_seconds = startup_timeout_seconds
        self._config: LauncherConfig | None = None
        self._paths: PortablePaths | None = None
        self._port_resolution: PortResolution | None = None
        self._process: subprocess.Popen[str] | None = None
        self._last_state = "idle"
        self._stdout_log: Path | None = None
        self._stderr_log: Path | None = None

    def prepare(self, config: LauncherConfig, paths: PortablePaths) -> None:
        paths.ensure_directories()
        self._config = config
        self._paths = paths
        self._port_resolution = PortResolver().resolve(config.bind_host, config.gateway_port)
        self._stdout_log = paths.logs_dir / "openclaw-runtime.out.log"
        self._stderr_log = paths.logs_dir / "openclaw-runtime.err.log"
        self._last_state = "ready"

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            return
        openclaw_dir = self._openclaw_dir()
        package_json = openclaw_dir / "package.json"
        if not package_json.exists():
            raise FileNotFoundError(f"OpenClaw runtime package not found: runtime/openclaw/package.json")
        if not self._stdout_log or not self._stderr_log:
            raise RuntimeError("Runtime must be prepared before it can start")

        with self._stdout_log.open("w", encoding="utf-8") as stdout_file, self._stderr_log.open("w", encoding="utf-8") as stderr_file:
            self._process = subprocess.Popen(
                self.build_command(),
                cwd=str(openclaw_dir),
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=self.build_environment(),
            )
        self._wait_until_ready()
        self._last_state = "running"

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
            )
        if self._process and self._process.poll() is not None:
            return RuntimeStatus(
                state="stopped",
                port=self._port_resolution.port,
                message=self._port_resolution.message,
                pid=self._process.pid,
            )
        return RuntimeStatus(state=self._last_state, port=self._port_resolution.port, message=self._port_resolution.message)

    def webui_url(self) -> str:
        if not self._config or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before URL can be resolved")
        return f"http://{self._config.bind_host}:{self._port_resolution.port + 2}"

    def healthcheck(self) -> RuntimeHealth:
        if not self._config or not self._port_resolution:
            return RuntimeHealth(ok=False, error="Runtime must be prepared before healthcheck")
        try:
            with socket.create_connection((self._config.bind_host, self._port_resolution.port), timeout=2):
                return RuntimeHealth(
                    ok=True,
                    details={
                        "gatewayPort": self._port_resolution.port,
                        "controlUiUrl": self.webui_url(),
                    },
                )
        except OSError as exc:
            return RuntimeHealth(ok=False, error=str(exc))

    def resolved_node_command(self) -> str:
        if not self._paths:
            raise RuntimeError("Runtime paths are not prepared")
        embedded_node = self._paths.runtime_dir / "node" / "node.exe"
        if embedded_node.exists():
            return str(embedded_node)
        return self.node_command

    def build_environment(self) -> dict[str, str]:
        if not self._config or not self._paths or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before environment can be built")
        return {
            **os.environ,
            "OPENCLAW_BIND_HOST": self._config.bind_host,
            "OPENCLAW_GATEWAY_PORT": str(self._port_resolution.port),
            "OPENCLAW_HOME": str(self._paths.state_dir),
            "OPENCLAW_STATE_DIR": str(self._paths.state_dir),
            "OPENCLAW_CONFIG_PATH": str(self._paths.config_file),
            "OPENCLAW_WORKSPACE_DIR": str(self._paths.workspace_dir),
            "OPENCLAW_LOG_DIR": str(self._paths.logs_dir),
            "OPENCLAW_CACHE_DIR": str(self._paths.cache_dir),
            "OPENCLAW_PROVIDER_ID": self._config.provider_id,
            "OPENCLAW_PROVIDER_NAME": self._config.provider_name,
            "OPENCLAW_BASE_URL": self._config.base_url,
            "OPENCLAW_MODEL": self._config.model,
            "OPENCLAW_API_KEY": self._read_api_key(),
            "HOME": str(self._paths.state_dir),
        }

    def build_command(self) -> list[str]:
        if not self._config or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before command can be built")
        return [
            self.resolved_node_command(),
            str(self._entrypoint_script()),
            "gateway",
            "run",
            "--port",
            str(self._port_resolution.port),
            "--bind",
            "loopback",
            "--allow-unconfigured",
        ]

    def _openclaw_dir(self) -> Path:
        if not self._paths:
            raise RuntimeError("Runtime paths are not prepared")
        return self._paths.runtime_dir / "openclaw"

    def _entrypoint_script(self) -> Path:
        openclaw_dir = self._openclaw_dir()
        candidates = (
            openclaw_dir / "openclaw.mjs",
            openclaw_dir / "server.js",
            openclaw_dir / "dist" / "server.js",
            openclaw_dir / "dist" / "index.js",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError("OpenClaw runtime entrypoint not found under runtime/openclaw")

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + self.startup_timeout_seconds
        while time.monotonic() < deadline:
            if self._process and self._process.poll() is not None:
                raise RuntimeError("OpenClaw runtime exited before becoming healthy")
            health = self.healthcheck()
            if health.ok:
                return
            time.sleep(0.5)
        raise TimeoutError("OpenClaw runtime did not become healthy in time")

    def _read_api_key(self) -> str:
        if not self._paths or not self._paths.env_file.exists():
            return ""
        for line in self._paths.env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENCLAW_API_KEY="):
                return line.split("=", 1)[1]
        return ""
