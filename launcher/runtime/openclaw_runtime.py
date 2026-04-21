from __future__ import annotations

import json
import os
import hashlib
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths
from launcher.core.port_resolver import PortResolution, PortResolver
from launcher.runtime.base import RuntimeAdapter, RuntimeHealth, RuntimeStatus


class OpenClawRuntimeAdapter(RuntimeAdapter):
    def __init__(
        self,
        node_command: str = "node",
        startup_timeout_seconds: float = 90,
        health_poll_interval_seconds: float = 0.5,
    ) -> None:
        self.node_command = node_command
        self.startup_timeout_seconds = startup_timeout_seconds
        self.health_poll_interval_seconds = health_poll_interval_seconds
        self._config: LauncherConfig | None = None
        self._paths: PortablePaths | None = None
        self._port_resolution: PortResolution | None = None
        self._process: subprocess.Popen[str] | None = None
        self._last_state = "idle"
        self._stdout_log: Path | None = None
        self._stderr_log: Path | None = None
        self._started_at_monotonic: float | None = None
        self._runtime_config_patch: dict[str, object] = {}
        self._runtime_env: dict[str, str] = {}
        self._openclaw_runtime_dir: Path | None = None

    def prepare(
        self,
        config: LauncherConfig,
        paths: PortablePaths,
        runtime_config_patch: dict[str, object] | None = None,
        runtime_env: dict[str, str] | None = None,
    ) -> None:
        paths.ensure_directories()
        self._config = config
        self._paths = paths
        self._port_resolution = PortResolver().resolve(config.bind_host, config.gateway_port)
        self._stdout_log = paths.logs_dir / "openclaw-runtime.out.log"
        self._stderr_log = paths.logs_dir / "openclaw-runtime.err.log"
        self._runtime_config_patch = runtime_config_patch or {}
        self._runtime_env = runtime_env or {}
        self._openclaw_runtime_dir = self._resolve_openclaw_runtime_dir()
        self._ensure_root_runtime_dependencies()
        self._apply_runtime_config_patch()
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
                creationflags=self._startup_creationflags(),
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

    def _startup_creationflags(self) -> int:
        if os.name != "nt":
            return 0
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def webui_url(self) -> str:
        if not self._config or not self._port_resolution:
            raise RuntimeError("Runtime must be prepared before URL can be resolved")
        return f"http://{self._config.bind_host}:{self._port_resolution.port}/#token={quote(self._webui_token(), safe='')}"

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
            "OPENCLAW_CONFIG_PATH": str(self._paths.runtime_config_file),
            "OPENCLAW_WORKSPACE_DIR": str(self._paths.workspace_dir),
            "OPENCLAW_LOG_DIR": str(self._paths.logs_dir),
            "OPENCLAW_CACHE_DIR": str(self._paths.cache_dir),
            "OPENCLAW_PROVIDER_ID": self._config.provider_id,
            "OPENCLAW_PROVIDER_NAME": self._config.provider_name,
            "OPENCLAW_BASE_URL": self._config.base_url,
            "OPENCLAW_MODEL": self._config.model,
            "OPENCLAW_API_KEY": self._read_api_key(),
            "HOME": str(self._paths.state_dir),
            **self._runtime_env,
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
        return self._openclaw_runtime_dir or (self._paths.runtime_dir / "openclaw")

    def _resolve_openclaw_runtime_dir(self) -> Path:
        if not self._paths:
            raise RuntimeError("Runtime paths are not prepared")
        source_dir = self._paths.runtime_dir / "openclaw"
        if not self._should_stage_runtime(source_dir):
            return source_dir
        if not source_dir.exists():
            return source_dir
        cache_key = self._runtime_cache_key(source_dir)
        cache_parent = self._paths.cache_dir / "runtime"
        target_dir = cache_parent / f"openclaw-{cache_key}"
        if self._is_usable_cached_runtime(target_dir):
            return target_dir
        staging_dir = cache_parent / f".{target_dir.name}.staging-{os.getpid()}"
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        cache_parent.mkdir(parents=True, exist_ok=True)
        _copy_runtime_tree(source_dir, staging_dir)
        (staging_dir / ".openclaw-portable-cache.json").write_text(
            json.dumps(
                {
                    "source": str(source_dir),
                    "cacheKey": cache_key,
                    "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        staging_dir.replace(target_dir)
        return target_dir

    def _should_stage_runtime(self, source_dir: Path) -> bool:
        override = os.environ.get("OPENCLAW_PORTABLE_STAGE_RUNTIME", "").strip().lower()
        if override in {"1", "true", "yes", "on", "always"}:
            return True
        if override in {"0", "false", "no", "off", "never"}:
            return False
        if not self._paths:
            return False
        return _is_removable_path(self._paths.project_root) and source_dir.exists()

    def _runtime_cache_key(self, source_dir: Path) -> str:
        if not self._paths:
            raise RuntimeError("Runtime paths are not prepared")
        digest = hashlib.sha256()
        candidates = (
            self._paths.project_root / "update-manifest.json",
            self._paths.project_root / "version.json",
            source_dir / "package.json",
            source_dir / "package-lock.json",
            source_dir / "node_modules" / ".package-lock.json",
            source_dir / "openclaw.mjs",
        )
        for candidate in candidates:
            if not candidate.exists():
                continue
            stat = candidate.stat()
            digest.update(str(candidate.relative_to(self._paths.project_root)).encode("utf-8", errors="replace"))
            digest.update(str(stat.st_size).encode("ascii"))
            digest.update(str(stat.st_mtime_ns).encode("ascii"))
            if stat.st_size <= 2_000_000:
                digest.update(candidate.read_bytes())
        return digest.hexdigest()[:16]

    def _is_usable_cached_runtime(self, target_dir: Path) -> bool:
        return (
            target_dir.exists()
            and (target_dir / "package.json").exists()
            and (target_dir / "openclaw.mjs").exists()
            and (target_dir / ".openclaw-portable-cache.json").exists()
        )

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
            time.sleep(self.health_poll_interval_seconds)
        raise TimeoutError("OpenClaw runtime did not become healthy in time")

    def _read_api_key(self) -> str:
        if not self._paths or not self._paths.env_file.exists():
            return ""
        for line in self._paths.env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENCLAW_API_KEY="):
                return line.split("=", 1)[1]
        return ""

    def _apply_runtime_config_patch(self) -> None:
        if not self._paths or not self._runtime_config_patch:
            return
        current_config = self._load_runtime_config()
        merged_config = self._deep_merge(current_config, self._runtime_config_patch)
        self._paths.runtime_config_file.write_text(
            json.dumps(merged_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _webui_token(self) -> str:
        runtime_config = self._load_runtime_config()
        gateway = runtime_config.get("gateway")
        if not isinstance(gateway, dict):
            return "uclaw"
        auth = gateway.get("auth")
        if not isinstance(auth, dict):
            return "uclaw"
        token = auth.get("token")
        if not isinstance(token, str) or not token.strip():
            return "uclaw"
        return token.strip()

    def _load_runtime_config(self) -> dict[str, object]:
        if not self._paths or not self._paths.runtime_config_file.exists():
            return {}
        try:
            payload = json.loads(self._paths.runtime_config_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def _deep_merge(self, base: dict[str, object], patch: dict[str, object]) -> dict[str, object]:
        merged: dict[str, object] = dict(base)
        for key, value in patch.items():
            existing_value = merged.get(key)
            if isinstance(value, dict) and isinstance(existing_value, dict):
                merged[key] = self._deep_merge(existing_value, value)
                continue
            merged[key] = value
        return merged

    def _ensure_root_runtime_dependencies(self) -> None:
        openclaw_dir = self._openclaw_dir()
        extensions_dir = openclaw_dir / "dist" / "extensions"
        if not extensions_dir.exists():
            return
        target_node_modules_dir = openclaw_dir / "node_modules"
        visited_packages: set[str] = set()
        for extension_dir in extensions_dir.iterdir():
            node_modules_dir = extension_dir / "node_modules"
            if not node_modules_dir.exists():
                continue
            for package_dir in _iter_node_modules_package_dirs(node_modules_dir):
                self._bridge_runtime_dependency_tree(
                    package_dir,
                    source_node_modules_dir=node_modules_dir,
                    target_node_modules_dir=target_node_modules_dir,
                    visited_packages=visited_packages,
                )

    def _bridge_runtime_dependency_tree(
        self,
        package_dir: Path,
        *,
        source_node_modules_dir: Path,
        target_node_modules_dir: Path,
        visited_packages: set[str],
    ) -> None:
        package_name = _package_name_for_dir(package_dir)
        if not package_name or package_name in visited_packages:
            return
        visited_packages.add(package_name)

        target_dir = _node_modules_package_dir(target_node_modules_dir, package_name)
        if not target_dir.exists():
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(package_dir, target_dir)

        package_manifest = _load_package_manifest(package_dir)
        for dependency_name in _runtime_dependency_names(package_manifest):
            dependency_dir = _resolve_dependency_dir(package_dir, source_node_modules_dir, dependency_name)
            if dependency_dir is None:
                continue
            self._bridge_runtime_dependency_tree(
                dependency_dir,
                source_node_modules_dir=source_node_modules_dir,
                target_node_modules_dir=target_node_modules_dir,
                visited_packages=visited_packages,
            )


def _is_removable_path(path: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        resolved = path.resolve()
        root = resolved.anchor or str(resolved)
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(str(Path(root)))
    except Exception:  # noqa: BLE001
        return False
    return drive_type == 2


def _copy_runtime_tree(source_dir: Path, target_dir: Path) -> None:
    robocopy = shutil.which("robocopy") if os.name == "nt" else None
    if robocopy:
        target_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [
                robocopy,
                str(source_dir),
                str(target_dir),
                "/E",
                "/R:1",
                "/W:1",
                "/MT:16",
                "/NFL",
                "/NDL",
                "/NJH",
                "/NJS",
                "/NP",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode >= 8:
            raise RuntimeError(f"Failed to stage OpenClaw runtime cache with robocopy: {completed.stderr.strip()}")
        return
    shutil.copytree(source_dir, target_dir)


def _find_node_modules_dir(package_dir: Path) -> Path | None:
    current = package_dir.parent
    while True:
        if current.name == "node_modules":
            return current
        if current == current.parent:
            return None
        current = current.parent


def _iter_node_modules_package_dirs(node_modules_dir: Path) -> tuple[Path, ...]:
    package_dirs: list[Path] = []
    for child in node_modules_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("@"):
            for scoped_child in child.iterdir():
                if scoped_child.is_dir():
                    package_dirs.append(scoped_child)
            continue
        package_dirs.append(child)
    return tuple(package_dirs)


def _package_name_for_dir(package_dir: Path) -> str | None:
    manifest = _load_package_manifest(package_dir)
    package_name = manifest.get("name")
    if isinstance(package_name, str) and package_name.strip():
        return package_name.strip()
    package_leaf = package_dir.name
    parent_name = package_dir.parent.name
    if parent_name.startswith("@"):
        return f"{parent_name}/{package_leaf}"
    if package_leaf:
        return package_leaf
    return None


def _node_modules_package_dir(node_modules_dir: Path, package_name: str) -> Path:
    if package_name.startswith("@"):
        scope, leaf = package_name.split("/", 1)
        return node_modules_dir / scope / leaf
    return node_modules_dir / package_name


def _load_package_manifest(package_dir: Path) -> dict[str, object]:
    manifest_path = package_dir / "package.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _runtime_dependency_names(package_manifest: dict[str, object]) -> tuple[str, ...]:
    runtime_sections = ("dependencies", "optionalDependencies")
    names: list[str] = []
    for section_name in runtime_sections:
        section = package_manifest.get(section_name)
        if not isinstance(section, dict):
            continue
        for dependency_name in section:
            if isinstance(dependency_name, str) and dependency_name.strip():
                names.append(dependency_name.strip())
    return tuple(names)


def _resolve_dependency_dir(package_dir: Path, source_node_modules_dir: Path, dependency_name: str) -> Path | None:
    nested_node_modules_dir = package_dir / "node_modules"
    candidates = (
        _node_modules_package_dir(nested_node_modules_dir, dependency_name),
        _node_modules_package_dir(source_node_modules_dir, dependency_name),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
