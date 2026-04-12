# Feishu Private Chat Channel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a launcher-first Feishu private-chat MVP that lets users configure Feishu credentials, validate them, enable the channel, and route real private messages through the bundled OpenClaw Feishu plugin.

**Architecture:** Keep launcher responsibilities limited to config persistence, connection testing, runtime orchestration, status projection, diagnostics redaction, and offline help. Reuse the bundled OpenClaw runtime Feishu extension by mapping launcher-managed channel config into `state/openclaw.json` plus channel env vars, then reflect runtime readiness back into launcher-visible status files and UI.

**Tech Stack:** Python 3, PySide6, unittest, bundled OpenClaw runtime (`runtime/openclaw`), JSON state files under `state/channels/feishu`, Feishu tenant token HTTP API via `urllib.request`

---

## File Structure

**Create:**
- `launcher/services/feishu_channel.py` - Feishu channel storage, validation, runtime config projection, and status mapping service.
- `assets/guide/setup-feishu.html` - Offline setup guide linked from launcher UI.
- `tests/test_feishu_channel_service.py` - Unit tests for config/status persistence, token validation, runtime projection, and diagnostics redaction.

**Modify:**
- `launcher/core/paths.py` - Add canonical Feishu channel paths.
- `launcher/models.py` - Add launcher-facing Feishu channel view model.
- `launcher/services/controller.py` - Compose `FeishuChannelService`, expose save/test/enable/disable/read APIs, and inject projected channel config into runtime prepare flow.
- `launcher/runtime/openclaw_runtime.py` - Merge Feishu env vars and runtime config into `state/openclaw.json` before launch.
- `launcher/services/diagnostics_export.py` - Include redacted Feishu channel config/status in exported diagnostics.
- `launcher/ui/main_window.py` - Add a Feishu channel card with fields, actions, and status text.
- `launcher/app.py` - Bind Feishu UI events to controller actions and refresh UI state after channel mutations.
- `tests/test_launcher_controller.py` - Controller integration coverage for Feishu lifecycle and view-state mapping.
- `tests/test_diagnostics_export.py` - Diagnostics redaction coverage for Feishu data.
- `tests/test_launcher_app.py` - UI busy-state and action wiring coverage.

**Existing runtime references to preserve:**
- `runtime/openclaw/dist/extensions/feishu/openclaw.plugin.json`
- `runtime/openclaw/dist/extensions/feishu/api.js`
- `runtime/openclaw/package.json`

## Runtime Contract Assumptions

- The bundled runtime already ships a Feishu extension with `id: "feishu"` and channel env vars `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_VERIFICATION_TOKEN`, and `FEISHU_ENCRYPT_KEY`.
- Launcher-owned Feishu state lives in:
  - `state/channels/feishu/config.json`
  - `state/channels/feishu/status.json`
- Runtime-owned Feishu activation is projected into the portable runtime config at `state/openclaw.json`.
- Initial MVP uses a single default account:

```json
{
  "channels": {
    "feishu": {
      "defaultAccount": "default",
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "enabled": true,
      "accounts": {
        "default": {
          "enabled": true,
          "connectionMode": "websocket"
        }
      }
    }
  }
}
```

- Runtime env projection mirrors the same account for compatibility:

```text
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
```

### Task 1: Add Feishu Pathing And Channel Storage Service

**Files:**
- Modify: `launcher/core/paths.py`
- Create: `launcher/services/feishu_channel.py`
- Test: `tests/test_feishu_channel_service.py`

- [ ] **Step 1: Write the failing storage-path test**

```python
def test_feishu_paths_are_exposed_from_portable_paths() -> None:
    paths = PortablePaths.for_root(Path("C:/tmp/OpenClaw-Portable"))

    assert paths.feishu_channel_dir == Path("C:/tmp/OpenClaw-Portable/state/channels/feishu")
    assert paths.feishu_channel_config_file == paths.feishu_channel_dir / "config.json"
    assert paths.feishu_channel_status_file == paths.feishu_channel_dir / "status.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_feishu_channel_service.FeishuChannelServiceTests.test_feishu_paths_are_exposed_from_portable_paths -v`
Expected: FAIL with `AttributeError: 'PortablePaths' object has no attribute 'feishu_channel_dir'`

- [ ] **Step 3: Add the new path properties and directory creation**

```python
@dataclass(frozen=True)
class PortablePaths:
    project_root: Path
    runtime_dir: Path
    state_dir: Path
    assets_dir: Path
    tools_dir: Path
    temp_root: Path
    logs_dir: Path
    cache_dir: Path
    config_file: Path
    env_file: Path
    provider_templates_dir: Path
    workspace_dir: Path
    feishu_channel_dir: Path
    feishu_channel_config_file: Path
    feishu_channel_status_file: Path

    @classmethod
    def for_root(cls, project_root: Path, temp_base: Path | None = None) -> "PortablePaths":
        resolved_temp_base = temp_base or Path(os.environ.get("TEMP") or tempfile.gettempdir())
        temp_root = resolved_temp_base / "OpenClawPortable"
        state_dir = project_root / "state"
        feishu_channel_dir = state_dir / "channels" / "feishu"
        return cls(
            project_root=project_root,
            runtime_dir=project_root / "runtime",
            state_dir=state_dir,
            assets_dir=project_root / "assets",
            tools_dir=project_root / "tools",
            temp_root=temp_root,
            logs_dir=temp_root / "logs",
            cache_dir=temp_root / "cache",
            config_file=state_dir / "openclaw.json",
            env_file=state_dir / ".env",
            provider_templates_dir=state_dir / "provider-templates",
            workspace_dir=state_dir / "workspace",
            feishu_channel_dir=feishu_channel_dir,
            feishu_channel_config_file=feishu_channel_dir / "config.json",
            feishu_channel_status_file=feishu_channel_dir / "status.json",
        )

    def ensure_directories(self) -> None:
        directories = (
            self.project_root,
            self.runtime_dir,
            self.state_dir,
            self.assets_dir,
            self.tools_dir,
            self.temp_root,
            self.logs_dir,
            self.cache_dir,
            self.provider_templates_dir,
            self.workspace_dir,
            self.workspace_dir / "skills",
            self.workspace_dir / "memory",
            self.state_dir / "sessions",
            self.state_dir / "channels",
            self.state_dir / "backups",
            self.feishu_channel_dir,
        )
```

- [ ] **Step 4: Write failing persistence tests for config and status**

```python
def test_service_saves_and_loads_feishu_config_and_status(self) -> None:
    service = FeishuChannelService(self.paths)
    config = FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True, bot_app_name="OpenClaw Bot")
    status = FeishuChannelStatus(state="pending_enable", last_error="", last_connected_at=None, last_message_at=None)

    service.save_config(config)
    service.save_status(status)

    self.assertEqual(service.load_config(), config)
    self.assertEqual(service.load_status(), status)
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python -m unittest tests.test_feishu_channel_service.FeishuChannelServiceTests.test_service_saves_and_loads_feishu_config_and_status -v`
Expected: FAIL with `ImportError` or `NameError` for `FeishuChannelService`

- [ ] **Step 6: Implement minimal storage dataclasses and service**

```python
@dataclass(frozen=True)
class FeishuChannelConfig:
    app_id: str = ""
    app_secret: str = ""
    enabled: bool = False
    bot_app_name: str = "OpenClaw Bot"
    last_validated_at: str | None = None

@dataclass(frozen=True)
class FeishuChannelStatus:
    state: str = "unconfigured"
    last_error: str = ""
    last_connected_at: str | None = None
    last_message_at: str | None = None

class FeishuChannelService:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def load_config(self) -> FeishuChannelConfig:
        if not self.paths.feishu_channel_config_file.exists():
            return FeishuChannelConfig()
        raw = json.loads(self.paths.feishu_channel_config_file.read_text(encoding="utf-8"))
        return FeishuChannelConfig(**raw)

    def save_config(self, config: FeishuChannelConfig) -> None:
        self.paths.ensure_directories()
        self.paths.feishu_channel_config_file.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_status(self) -> FeishuChannelStatus:
        if not self.paths.feishu_channel_status_file.exists():
            return FeishuChannelStatus()
        raw = json.loads(self.paths.feishu_channel_status_file.read_text(encoding="utf-8"))
        return FeishuChannelStatus(**raw)

    def save_status(self, status: FeishuChannelStatus) -> None:
        self.paths.ensure_directories()
        self.paths.feishu_channel_status_file.write_text(
            json.dumps(asdict(status), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

- [ ] **Step 7: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_feishu_channel_service -v`
Expected: PASS for pathing and persistence tests

- [ ] **Step 8: Commit**

```bash
git add launcher/core/paths.py launcher/services/feishu_channel.py tests/test_feishu_channel_service.py
git commit -m "feat: add feishu channel storage service"
```

### Task 2: Add Credential Validation And Runtime Projection

**Files:**
- Modify: `launcher/services/feishu_channel.py`
- Modify: `launcher/services/controller.py`
- Modify: `launcher/runtime/openclaw_runtime.py`
- Test: `tests/test_feishu_channel_service.py`
- Test: `tests/test_launcher_controller.py`

- [ ] **Step 1: Write the failing credential-validation test**

```python
@patch("launcher.services.feishu_channel.urlopen")
def test_validate_credentials_maps_success_to_pending_enable(self, mock_urlopen) -> None:
    mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"code":0,"tenant_access_token":"t-123"}'
    service = FeishuChannelService(self.paths)

    result = service.validate_credentials("cli_xxx", "secret")

    self.assertTrue(result.ok)
    self.assertEqual(result.state, "pending_enable")
    self.assertEqual(result.error_message, "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_feishu_channel_service.FeishuChannelServiceTests.test_validate_credentials_maps_success_to_pending_enable -v`
Expected: FAIL because `validate_credentials` does not exist

- [ ] **Step 3: Implement minimal Feishu tenant-token validation**

```python
@dataclass(frozen=True)
class FeishuValidationResult:
    ok: bool
    state: str
    error_message: str
    validated_at: str | None = None

def validate_credentials(self, app_id: str, app_secret: str) -> FeishuValidationResult:
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    request = Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return FeishuValidationResult(ok=False, state="invalid_config", error_message="配置无效，请检查 App ID / App Secret")
    if body.get("code") != 0 or not body.get("tenant_access_token"):
        return FeishuValidationResult(ok=False, state="invalid_config", error_message="配置无效，请检查 App ID / App Secret")
    return FeishuValidationResult(ok=True, state="pending_enable", error_message="", validated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z")
```

- [ ] **Step 4: Write the failing runtime-projection test**

```python
def test_project_runtime_config_includes_default_feishu_account(self) -> None:
    service = FeishuChannelService(self.paths)
    config = FeishuChannelConfig(app_id="cli_xxx", app_secret="secret", enabled=True)

    projected = service.build_runtime_projection(config)

    self.assertEqual(projected.env["FEISHU_APP_ID"], "cli_xxx")
    self.assertEqual(projected.env["FEISHU_APP_SECRET"], "secret")
    self.assertTrue(projected.config_patch["channels"]["feishu"]["enabled"])
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python -m unittest tests.test_feishu_channel_service.FeishuChannelServiceTests.test_project_runtime_config_includes_default_feishu_account -v`
Expected: FAIL because `build_runtime_projection` does not exist

- [ ] **Step 6: Implement runtime projection and adapter merge hook**

```python
@dataclass(frozen=True)
class FeishuRuntimeProjection:
    env: dict[str, str]
    config_patch: dict[str, object]

def build_runtime_projection(self, config: FeishuChannelConfig) -> FeishuRuntimeProjection:
    return FeishuRuntimeProjection(
        env={
            "FEISHU_APP_ID": config.app_id,
            "FEISHU_APP_SECRET": config.app_secret,
        },
        config_patch={
            "channels": {
                "feishu": {
                    "defaultAccount": "default",
                    "appId": config.app_id,
                    "appSecret": config.app_secret,
                    "enabled": config.enabled,
                    "accounts": {
                        "default": {
                            "enabled": config.enabled,
                            "connectionMode": "websocket",
                        }
                    },
                }
            }
        },
    )
```

```python
def prepare(self, config: LauncherConfig, paths: PortablePaths, runtime_config_patch: dict[str, object] | None = None, runtime_env: dict[str, str] | None = None) -> None:
    paths.ensure_directories()
    self._config = config
    self._paths = paths
    self._port_resolution = PortResolver().resolve(config.bind_host, config.gateway_port)
    self._stdout_log = paths.logs_dir / "openclaw-runtime.out.log"
    self._stderr_log = paths.logs_dir / "openclaw-runtime.err.log"
    self._runtime_config_patch = runtime_config_patch or {}
    self._runtime_env = runtime_env or {}
    self._write_runtime_config_patch()
    self._last_state = "ready"
```

```python
def build_environment(self) -> dict[str, str]:
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
        **self._runtime_env,
    }
```

- [ ] **Step 7: Write the failing controller orchestration test**

```python
def test_controller_passes_feishu_projection_into_runtime_prepare(self) -> None:
    runtime_adapter = FakeRuntimeAdapter()
    controller = LauncherController(self.paths, runtime_adapter=runtime_adapter, runtime_mode="openclaw")
    controller.save_feishu_channel("cli_xxx", "secret", "OpenClaw Bot")
    controller.enable_feishu_channel()
    controller.configure(make_config(), SensitiveConfig(api_key="sk-demo"))

    self.assertEqual(runtime_adapter.last_runtime_env["FEISHU_APP_ID"], "cli_xxx")
    self.assertTrue(runtime_adapter.last_runtime_config_patch["channels"]["feishu"]["enabled"])
```

- [ ] **Step 8: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_feishu_channel_service tests.test_launcher_controller -v`
Expected: PASS for validation, projection, and controller orchestration tests

- [ ] **Step 9: Commit**

```bash
git add launcher/services/feishu_channel.py launcher/services/controller.py launcher/runtime/openclaw_runtime.py tests/test_feishu_channel_service.py tests/test_launcher_controller.py
git commit -m "feat: project feishu channel config into runtime"
```

### Task 3: Persist Runtime Config Safely And Reflect Channel Status

**Files:**
- Modify: `launcher/runtime/openclaw_runtime.py`
- Modify: `launcher/services/feishu_channel.py`
- Modify: `launcher/services/controller.py`
- Test: `tests/test_feishu_channel_service.py`
- Test: `tests/test_openclaw_runtime_adapter.py`

- [ ] **Step 1: Write the failing runtime-config merge test**

```python
def test_prepare_merges_feishu_patch_into_state_openclaw_json(self) -> None:
    adapter = OpenClawRuntimeAdapter(node_command="node")
    adapter.prepare(
        make_config(),
        self.paths,
        runtime_config_patch={"channels": {"feishu": {"enabled": True}}},
        runtime_env={"FEISHU_APP_ID": "cli_xxx"},
    )

    merged = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
    self.assertTrue(merged["channels"]["feishu"]["enabled"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_openclaw_runtime_adapter.OpenClawRuntimeAdapterTests.test_prepare_merges_feishu_patch_into_state_openclaw_json -v`
Expected: FAIL because `prepare` does not write merged runtime config

- [ ] **Step 3: Implement non-destructive JSON merge before runtime start**

```python
def _write_runtime_config_patch(self) -> None:
    if not self._paths:
        raise RuntimeError("Runtime paths are not prepared")
    existing = {}
    if self._paths.config_file.exists():
        existing = json.loads(self._paths.config_file.read_text(encoding="utf-8"))
    merged = merge_dict(existing, self._runtime_config_patch)
    self._paths.config_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
```

```python
def merge_dict(base: dict[str, object], patch: dict[str, object]) -> dict[str, object]:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)  # type: ignore[arg-type]
        else:
            result[key] = value
    return result
```

- [ ] **Step 4: Write the failing channel-status mapping test**

```python
def test_status_transitions_to_connected_when_runtime_reports_running(self) -> None:
    service = FeishuChannelService(self.paths)

    service.refresh_runtime_status(runtime_state="running", runtime_message="feishu ready")

    self.assertEqual(service.load_status().state, "connected")
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python -m unittest tests.test_feishu_channel_service.FeishuChannelServiceTests.test_status_transitions_to_connected_when_runtime_reports_running -v`
Expected: FAIL because `refresh_runtime_status` does not exist

- [ ] **Step 6: Implement minimal launcher-owned status machine**

```python
def refresh_runtime_status(self, runtime_state: str, runtime_message: str = "") -> FeishuChannelStatus:
    current = self.load_status()
    if runtime_state == "running":
        next_status = FeishuChannelStatus(
            state="connected",
            last_error="",
            last_connected_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            last_message_at=current.last_message_at,
        )
    elif runtime_state in {"stopped", "idle"}:
        next_status = replace(current, state="pending_enable" if self.load_config().enabled else "unconfigured")
    else:
        next_status = replace(current, state="connection_failed", last_error="飞书连接失败，可查看诊断并重试")
    self.save_status(next_status)
    return next_status
```

- [ ] **Step 7: Make controller refresh Feishu status alongside normal view-state reads**

```python
def load_feishu_channel_state(self) -> FeishuChannelState:
    runtime_status = self.runtime_adapter.status()
    self.feishu_channel_service.refresh_runtime_status(runtime_status.state, runtime_status.message or "")
    return self.feishu_channel_service.build_view_state(runtime_running=runtime_status.state == "running")
```

- [ ] **Step 8: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_feishu_channel_service tests.test_openclaw_runtime_adapter tests.test_launcher_controller -v`
Expected: PASS for config merge and status-machine tests

- [ ] **Step 9: Commit**

```bash
git add launcher/runtime/openclaw_runtime.py launcher/services/feishu_channel.py launcher/services/controller.py tests/test_feishu_channel_service.py tests/test_openclaw_runtime_adapter.py tests/test_launcher_controller.py
git commit -m "feat: persist feishu runtime config and status"
```

### Task 4: Add Launcher View Model And Feishu Card UI

**Files:**
- Modify: `launcher/models.py`
- Modify: `launcher/ui/main_window.py`
- Modify: `launcher/app.py`
- Modify: `launcher/services/controller.py`
- Test: `tests/test_launcher_app.py`
- Test: `tests/test_launcher_controller.py`

- [ ] **Step 1: Write the failing model/UI test**

```python
def test_main_window_shows_feishu_channel_controls(self) -> None:
    window = OpenClawLauncherWindow()

    assert window.feishu_app_id_input is not None
    assert window.feishu_app_secret_input is not None
    assert window.test_feishu_button.text() == "测试连接"
    assert window.enable_feishu_button.text() == "启用飞书私聊"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_app.LauncherAppTests.test_main_window_shows_feishu_channel_controls -v`
Expected: FAIL because the Feishu widgets do not exist

- [ ] **Step 3: Add a dedicated launcher-facing channel model**

```python
@dataclass(frozen=True)
class FeishuChannelState:
    state_label: str
    detail: str
    app_id: str
    app_secret_masked: str
    enabled: bool
    last_validated_at: str
    last_connected_at: str
    last_message_at: str
```

- [ ] **Step 4: Add the Feishu card and action hooks in the main window**

```python
self.feishu_app_id_input = QLineEdit()
self.feishu_app_secret_input = QLineEdit()
self.feishu_app_secret_input.setEchoMode(QLineEdit.Password)
self.test_feishu_button = make_button("测试连接")
self.enable_feishu_button = make_button("启用飞书私聊")
self.disable_feishu_button = make_button("停用")
self.open_feishu_guide_button = make_button("接入帮助", subtle=True)
self.feishu_status_label = make_label("未配置", "HeroTitle", size=16, weight=700)
self.feishu_detail_label = make_label("填写 App ID / App Secret 后可测试连接。", "MutedText")
```

- [ ] **Step 5: Bind the new handlers in `launcher/app.py`**

```python
self.main_window.bind_handlers(
    on_start=self._handle_start,
    on_stop=self._handle_stop,
    on_restart=self._handle_restart,
    on_open_webui=self._handle_open_webui,
    on_export_diagnostics=self._handle_export_diagnostics,
    on_check_update=self._handle_check_update,
    on_import_update=self._handle_import_update,
    on_restore_update_backup=self._handle_restore_update_backup,
    on_factory_reset=self._handle_factory_reset,
    on_reconfigure=self.show_setup_wizard,
    on_save_feishu=self._save_feishu_channel,
    on_test_feishu=self._test_feishu_channel,
    on_enable_feishu=self._enable_feishu_channel,
    on_disable_feishu=self._disable_feishu_channel,
    on_open_feishu_guide=self._open_feishu_guide,
)
```

- [ ] **Step 6: Add controller APIs used by the UI**

```python
def save_feishu_channel(self, app_id: str, app_secret: str, bot_app_name: str = "OpenClaw Bot") -> FeishuChannelState:
    return self.feishu_channel_service.save_from_inputs(app_id, app_secret, bot_app_name)

def test_feishu_channel(self) -> FeishuChannelState:
    return self.feishu_channel_service.test_saved_config()

def enable_feishu_channel(self) -> FeishuChannelState:
    return self.feishu_channel_service.enable_saved_config()

def disable_feishu_channel(self) -> FeishuChannelState:
    return self.feishu_channel_service.disable()
```

- [ ] **Step 7: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_controller -v`
Expected: PASS for UI presence, handler wiring, and controller state tests

- [ ] **Step 8: Commit**

```bash
git add launcher/models.py launcher/ui/main_window.py launcher/app.py launcher/services/controller.py tests/test_launcher_app.py tests/test_launcher_controller.py
git commit -m "feat: add feishu channel card to launcher"
```

### Task 5: Add Diagnostics Redaction And Offline Help

**Files:**
- Modify: `launcher/services/diagnostics_export.py`
- Modify: `launcher/services/feishu_channel.py`
- Create: `assets/guide/setup-feishu.html`
- Test: `tests/test_diagnostics_export.py`
- Test: `tests/test_feishu_channel_service.py`

- [ ] **Step 1: Write the failing diagnostics-export test**

```python
def test_exports_redacted_feishu_channel_summary(self) -> None:
    service = FeishuChannelService(self.paths)
    service.save_config(FeishuChannelConfig(app_id="cli_xxx", app_secret="super-secret", enabled=True))
    service.save_status(FeishuChannelStatus(state="connected", last_error="", last_connected_at="2026-04-12T12:00:00Z", last_message_at=None))

    bundle_path = DiagnosticsExporter(self.paths, runtime_mode="openclaw").export_bundle()

    with zipfile.ZipFile(bundle_path) as archive:
        summary = json.loads(archive.read("config-summary.json").decode("utf-8"))

    self.assertEqual(summary["feishu"]["appId"], "cli_xxx")
    self.assertTrue(summary["feishu"]["appSecretConfigured"])
    self.assertNotIn("super-secret", json.dumps(summary, ensure_ascii=False))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_diagnostics_export.DiagnosticsExporterTests.test_exports_redacted_feishu_channel_summary -v`
Expected: FAIL because Feishu diagnostics fields are not exported

- [ ] **Step 3: Add redacted summary helpers**

```python
def build_diagnostics_summary(self) -> dict[str, object]:
    config = self.load_config()
    status = self.load_status()
    return {
        "configured": bool(config.app_id or config.app_secret),
        "enabled": config.enabled,
        "appId": config.app_id,
        "appSecretConfigured": bool(config.app_secret),
        "state": status.state,
        "lastError": status.last_error,
        "lastValidatedAt": config.last_validated_at,
        "lastConnectedAt": status.last_connected_at,
        "lastMessageAt": status.last_message_at,
    }
```

- [ ] **Step 4: Inject the Feishu summary into diagnostics export**

```python
return {
    "firstRun": False,
    "runtimeMode": self.runtime_mode,
    "providerId": config.provider_id,
    "providerName": config.provider_name,
    "baseUrl": config.base_url,
    "model": config.model,
    "gatewayPort": config.gateway_port,
    "bindHost": config.bind_host,
    "firstRunCompleted": config.first_run_completed,
    "apiKeyConfigured": bool(sensitive.api_key),
    "adminPasswordConfigured": bool(config.admin_password),
    "feishu": self.feishu_channel_service.build_diagnostics_summary(),
}
```

- [ ] **Step 5: Add the offline help page**

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>飞书私聊接入帮助</title>
</head>
<body>
  <h1>飞书私聊接入帮助</h1>
  <ol>
    <li>在飞书开放平台创建企业自建应用。</li>
    <li>开启机器人能力并记录 App ID / App Secret。</li>
    <li>确认私聊可用性与事件订阅配置。</li>
    <li>回到启动器填写凭据，点击“测试连接”。</li>
    <li>测试通过后启用飞书私聊，再启动 OpenClaw。</li>
  </ol>
</body>
</html>
```

- [ ] **Step 6: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_diagnostics_export tests.test_feishu_channel_service -v`
Expected: PASS for diagnostics redaction and guide-path assertions

- [ ] **Step 7: Commit**

```bash
git add launcher/services/diagnostics_export.py launcher/services/feishu_channel.py assets/guide/setup-feishu.html tests/test_diagnostics_export.py tests/test_feishu_channel_service.py
git commit -m "feat: add feishu diagnostics and offline guide"
```

### Task 6: End-To-End Launcher Polish And Regression Coverage

**Files:**
- Modify: `launcher/app.py`
- Modify: `launcher/ui/main_window.py`
- Modify: `launcher/services/controller.py`
- Test: `tests/test_launcher_app.py`
- Test: `tests/test_launcher_controller.py`
- Test: `tests/test_feishu_channel_service.py`

- [ ] **Step 1: Write the failing busy-state regression test**

```python
def test_test_feishu_action_disables_button_while_running(self) -> None:
    app = object.__new__(OpenClawLauncherApplication)
    app.main_window = OpenClawLauncherWindow()

    app._set_action_busy("test_feishu", True)

    self.assertFalse(app.main_window.test_feishu_button.isEnabled())
    self.assertEqual(app.main_window.test_feishu_button.text(), "正在测试...")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_app.LauncherAppTests.test_test_feishu_action_disables_button_while_running -v`
Expected: FAIL because Feishu action busy state is not mapped

- [ ] **Step 3: Extend busy-state handling and user-visible Chinese status copy**

```python
if action == "test_feishu":
    button.setText("正在测试..." if busy else "测试连接")
elif action == "enable_feishu":
    button.setText("正在启用..." if busy else "启用飞书私聊")
elif action == "disable_feishu":
    button.setText("正在停用..." if busy else "停用")
```

- [ ] **Step 4: Add regression tests for disable/reset flows**

```python
def test_disable_feishu_channel_clears_enabled_flag_but_keeps_credentials(self) -> None:
    controller = LauncherController(self.paths, runtime_mode="openclaw")
    controller.save_feishu_channel("cli_xxx", "secret")
    controller.enable_feishu_channel()

    state = controller.disable_feishu_channel()

    self.assertFalse(state.enabled)
    self.assertEqual(controller.feishu_channel_service.load_config().app_id, "cli_xxx")
```

- [ ] **Step 5: Run full targeted verification**

Run: `python -m unittest tests.test_feishu_channel_service tests.test_launcher_controller tests.test_launcher_app tests.test_diagnostics_export tests.test_openclaw_runtime_adapter -v`
Expected: PASS for all Feishu-related tests

- [ ] **Step 6: Run full project verification**

Run: `python -m unittest discover -s tests`
Expected: PASS with Feishu coverage added and no regression in existing launcher/update/runtime tests

- [ ] **Step 7: Manual acceptance walkthrough**

Run:
```bash
python main.py
```

Expected:
- Launcher shows Feishu channel card.
- Saving `App ID / App Secret` persists `state/channels/feishu/config.json`.
- “测试连接” maps valid creds to `待启用`.
- “启用飞书私聊” updates `state/openclaw.json` with `channels.feishu`.
- Starting runtime transitions Feishu status from `连接中` to `已连接` on healthy runtime.
- Diagnostics export includes redacted Feishu summary.

- [ ] **Step 8: Commit**

```bash
git add launcher/app.py launcher/ui/main_window.py launcher/services/controller.py tests/test_launcher_app.py tests/test_launcher_controller.py tests/test_feishu_channel_service.py
git commit -m "feat: complete feishu private chat launcher flow"
```

## Final Verification Checklist

- [ ] `python -m unittest tests.test_feishu_channel_service -v`
- [ ] `python -m unittest tests.test_launcher_controller -v`
- [ ] `python -m unittest tests.test_launcher_app -v`
- [ ] `python -m unittest tests.test_diagnostics_export -v`
- [ ] `python -m unittest tests.test_openclaw_runtime_adapter -v`
- [ ] `python -m unittest discover -s tests`
- [ ] Manual launcher walkthrough against a real Feishu app in private chat mode

## Notes For Execution

- Prefer launcher-managed single-account Feishu support only; do not expand into multi-account or group-chat behavior during this plan.
- Keep secrets redacted everywhere except `state/channels/feishu/config.json` and transient runtime env.
- Do not invent a Python message bridge. If runtime plugin behavior appears missing, stop and verify the bundled OpenClaw Feishu extension contract before extending scope.
- Reuse the existing `%TEMP%\\OpenClawPortable\\logs` pattern for launcher/runtime diagnostics.
