from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


WECHAT_PLUGIN_RELATIVE_ROOTS = (
    Path("state") / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin",
    Path("state") / ".openclaw" / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin",
    Path("state") / "extensions" / "openclaw-weixin",
)

REGISTER_FAILURE_MARKERS = (
    "openclaw-weixin failed during register",
    "Unable to resolve plugin runtime module",
)


@dataclass(frozen=True)
class WechatPluginGatewaySmokeResult:
    ok: bool
    package_root: Path
    port: int | None
    error: str
    stdout_log: Path
    stderr_log: Path
    stderr_tail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "packageRoot": str(self.package_root),
            "port": self.port,
            "error": self.error,
            "stdoutLog": str(self.stdout_log),
            "stderrLog": str(self.stderr_log),
            "stderrTail": self.stderr_tail,
        }


def find_wechat_plugin_root(package_root: Path) -> Path | None:
    for relative_root in WECHAT_PLUGIN_RELATIVE_ROOTS:
        candidate = package_root / relative_root
        if (candidate / "dist" / "index.js").exists():
            return candidate
    return None


def detect_wechat_register_failure(stderr_text: str) -> bool:
    return any(marker in stderr_text for marker in REGISTER_FAILURE_MARKERS)


def verify_wechat_plugin_smoke_prerequisites(package_root: Path) -> list[str]:
    missing: list[str] = []
    runtime_root = package_root / "runtime" / "openclaw"
    manifest_path = runtime_root / "package.json"
    if not manifest_path.exists():
        missing.append("runtime/openclaw/package.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
        if manifest.get("name") != "openclaw":
            missing.append("runtime/openclaw/package.json:name=openclaw")
    if not (runtime_root / "dist" / "plugins" / "runtime" / "index.js").exists():
        missing.append("runtime/openclaw/dist/plugins/runtime/index.js")
    if find_wechat_plugin_root(package_root) is None:
        missing.append("state npm @tencent-weixin/openclaw-weixin dist/index.js")
    if not (package_root / "state" / "runtime" / "openclaw.json").exists():
        missing.append("state/runtime/openclaw.json")
    return missing


def run_wechat_plugin_gateway_smoke(
    package_root: Path,
    *,
    timeout_seconds: float = 45.0,
    post_ready_wait_seconds: float = 3.0,
) -> WechatPluginGatewaySmokeResult:
    package_root = package_root.resolve()
    logs_dir = package_root / "state" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = logs_dir / "wechat-plugin-gateway-smoke.out.log"
    stderr_log = logs_dir / "wechat-plugin-gateway-smoke.err.log"

    missing = verify_wechat_plugin_smoke_prerequisites(package_root)
    if missing:
        return WechatPluginGatewaySmokeResult(
            ok=False,
            package_root=package_root,
            port=None,
            error=f"Missing smoke prerequisites: {', '.join(missing)}",
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            stderr_tail="",
        )

    node_command = _resolve_node_command(package_root)
    entrypoint = package_root / "runtime" / "openclaw" / "openclaw.mjs"
    port = _reserve_free_port()
    env = _build_smoke_environment(package_root, port)
    process: subprocess.Popen[str] | None = None
    try:
        with stdout_log.open("w", encoding="utf-8") as stdout_file, stderr_log.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                [
                    str(node_command),
                    str(entrypoint),
                    "gateway",
                    "run",
                    "--port",
                    str(port),
                    "--bind",
                    "loopback",
                    "--allow-unconfigured",
                ],
                cwd=str(package_root / "runtime" / "openclaw"),
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                creationflags=_startup_creationflags(),
            )
        ready = _wait_until_http_ready(port, process=process, timeout_seconds=timeout_seconds)
        if ready:
            time.sleep(max(0.0, post_ready_wait_seconds))
        stderr_tail = _read_tail(stderr_log)
        if not ready:
            return WechatPluginGatewaySmokeResult(False, package_root, port, "Gateway did not become HTTP ready.", stdout_log, stderr_log, stderr_tail)
        if detect_wechat_register_failure(stderr_tail):
            return WechatPluginGatewaySmokeResult(False, package_root, port, "WeChat plugin failed during gateway register.", stdout_log, stderr_log, stderr_tail)
        return WechatPluginGatewaySmokeResult(True, package_root, port, "", stdout_log, stderr_log, stderr_tail)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _resolve_node_command(package_root: Path) -> Path | str:
    embedded_node = package_root / "runtime" / "node" / "node.exe"
    if embedded_node.exists():
        return embedded_node
    return "node"


def _build_smoke_environment(package_root: Path, port: int) -> dict[str, str]:
    state_dir = package_root / "state"
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().endswith("_PROXY") and key.upper() != "NO_PROXY"
    }
    env.update(
        {
            "OPENCLAW_HOME": str(state_dir),
            "OPENCLAW_STATE_DIR": str(state_dir),
            "OPENCLAW_CONFIG_PATH": str(state_dir / "runtime" / "openclaw.json"),
            "OPENCLAW_WORKSPACE_DIR": str(state_dir / "workspace"),
            "OPENCLAW_LOG_DIR": str(state_dir / "logs"),
            "OPENCLAW_CACHE_DIR": str(state_dir / "cache"),
            "OPENCLAW_BIND_HOST": "127.0.0.1",
            "OPENCLAW_GATEWAY_PORT": str(port),
            "OPENCLAW_API_KEY": _read_api_key(state_dir / ".env"),
            "HOME": str(state_dir),
        }
    )
    return env


def _read_api_key(env_file: Path) -> str:
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines:
        if line.startswith("OPENCLAW_API_KEY="):
            return line.split("=", 1)[1]
    return ""


def _reserve_free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return int(port)


def _wait_until_http_ready(port: int, *, process: subprocess.Popen[str], timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(f"http://127.0.0.1:{port}/", timeout=2):
                return True
        except HTTPError:
            return True
        except (OSError, URLError):
            time.sleep(0.5)
    return False


def _read_tail(path: Path, *, max_chars: int = 8000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-max_chars:]


def _startup_creationflags() -> int:
    if os.name != "nt":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)
