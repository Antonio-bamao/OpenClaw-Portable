# Provider Bridge Runtime Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Bridge launcher-managed provider settings into OpenClaw-native runtime model selection and main-agent auth profiles so chat uses the selected vendor instead of falling back to unrelated defaults.

**Architecture:** Add a focused provider-bridge service that reads `LauncherConfig` plus `SensitiveConfig`, detects the effective vendor, generates an OpenClaw runtime config patch, and writes a launcher-owned `state/agents/main/agent/auth-profiles.json`. Integrate that bridge into controller prepare/reproject paths, then add the smallest possible UI surface by extending provider templates with `openai` and `anthropic`.

**Tech Stack:** Python 3.12, `unittest`, existing launcher controller/runtime services, bundled OpenClaw runtime config/auth store

---

### Task 1: Add Provider Bridge Detection And Projection Service

**Files:**
- Create: `launcher/services/provider_bridge.py`
- Create: `tests/test_provider_bridge.py`
- Modify: `launcher/core/paths.py`
- Test: `tests/test_core_services.py`

- [x] **Step 1: Write failing provider-bridge tests**

Add a new test module covering:

```python
import json
import shutil
import unittest
import uuid
from pathlib import Path

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.services.provider_bridge import ProviderBridge


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"provider-bridge-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config(
    *,
    provider_id: str,
    provider_name: str,
    base_url: str,
    model: str,
) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=base_url,
        model=model,
        gateway_port=18789,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


class ProviderBridgeTests(unittest.TestCase):
    def test_detects_qwen_from_dashscope_and_generates_runtime_primary_model(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="dashscope",
                    provider_name="通义千问",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-max",
                ),
                SensitiveConfig(api_key="sk-qwen"),
            )

            self.assertEqual(projection.provider_type, "qwen")
            self.assertEqual(projection.primary_model, "qwen/qwen-max")
            self.assertEqual(
                projection.runtime_config_patch["agents"]["defaults"]["model"]["primary"],
                "qwen/qwen-max",
            )
            self.assertEqual(projection.auth_profile_id, "qwen:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_detects_openai_from_provider_id(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            self.assertEqual(projection.provider_type, "openai")
            self.assertEqual(projection.primary_model, "openai/gpt-5.4")
            self.assertEqual(projection.auth_profile_id, "openai:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_detects_anthropic_from_api_base(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="anthropic",
                    provider_name="Anthropic",
                    base_url="https://api.anthropic.com",
                    model="claude-sonnet-4-6",
                ),
                SensitiveConfig(api_key="sk-ant"),
            )

            self.assertEqual(projection.provider_type, "anthropic")
            self.assertEqual(projection.primary_model, "anthropic/claude-sonnet-4-6")
            self.assertEqual(projection.auth_profile_id, "anthropic:launcher")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_falls_back_to_custom_compatible_for_unknown_openai_style_endpoint(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)
            projection = bridge.build_projection(
                make_config(
                    provider_id="custom",
                    provider_name="自定义",
                    base_url="https://llm.example.com/v1",
                    model="acme-chat-pro",
                ),
                SensitiveConfig(api_key="sk-custom"),
            )

            self.assertEqual(projection.provider_type, "custom-compatible")
            self.assertEqual(projection.auth_profile_id, "custom-compatible:launcher")
            self.assertIn("models", projection.runtime_config_patch)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
```

Also extend `tests/test_core_services.py` with new path helper assertions for:

```python
self.assertEqual(paths.main_agent_dir, state_dir / "agents" / "main" / "agent")
self.assertEqual(paths.main_agent_auth_profiles_file, state_dir / "agents" / "main" / "agent" / "auth-profiles.json")
```

- [x] **Step 2: Run the new focused tests and verify they fail**

Run: `python -m unittest tests.test_provider_bridge tests.test_core_services`

Expected: FAIL because `ProviderBridge` and the new path helpers do not exist yet.

- [x] **Step 3: Add the provider bridge and path helpers**

Create `launcher/services/provider_bridge.py` with a small dataclass-based interface:

```python
from __future__ import annotations

import json
from dataclasses import dataclass

from launcher.core.config_store import LauncherConfig, SensitiveConfig
from launcher.core.paths import PortablePaths


@dataclass(frozen=True)
class ProviderBridgeProjection:
    provider_type: str
    primary_model: str
    runtime_config_patch: dict[str, object]
    auth_profile_id: str | None
    auth_profiles_document: dict[str, object] | None


class ProviderBridge:
    def __init__(self, paths: PortablePaths) -> None:
        self.paths = paths

    def build_projection(
        self,
        config: LauncherConfig,
        sensitive: SensitiveConfig,
    ) -> ProviderBridgeProjection:
        provider_type = self._detect_provider_type(config)
        primary_model = self._resolve_primary_model(provider_type, config.model)
        runtime_patch = self._build_runtime_patch(provider_type, config, primary_model)
        auth_profile_id, auth_doc = self._build_auth_document(provider_type, sensitive.api_key)
        return ProviderBridgeProjection(
            provider_type=provider_type,
            primary_model=primary_model,
            runtime_config_patch=runtime_patch,
            auth_profile_id=auth_profile_id,
            auth_profiles_document=auth_doc,
        )

    def apply(self, config: LauncherConfig, sensitive: SensitiveConfig) -> ProviderBridgeProjection:
        projection = self.build_projection(config, sensitive)
        self.paths.ensure_directories()
        if projection.auth_profiles_document is not None:
            self._save_auth_profiles_document(projection.auth_profiles_document)
        return projection
```

Implement:

- provider detection by `provider_id`, then `base_url`, then `model`
- canonical model mapping for `openai`, `anthropic`, `qwen`, `deepseek`, `openrouter`
- `custom-compatible` runtime patch under `models.providers`
- merge-safe auth-profile generation using launcher-owned IDs only

Add path helpers in `launcher/core/paths.py`:

```python
    main_agent_dir: Path | None = None
    main_agent_auth_profiles_file: Path | None = None
```

and derive them in `__post_init__`.

- [x] **Step 4: Run the focused tests again**

Run: `python -m unittest tests.test_provider_bridge tests.test_core_services`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add launcher/core/paths.py launcher/services/provider_bridge.py tests/test_core_services.py tests/test_provider_bridge.py
git commit -m "feat: add provider bridge projection service"
```

### Task 2: Persist Main-Agent Auth Profiles Safely

**Files:**
- Modify: `launcher/services/provider_bridge.py`
- Modify: `tests/test_provider_bridge.py`

- [x] **Step 1: Add failing tests for auth-profile merge and overwrite safety**

Extend `tests/test_provider_bridge.py` with:

```python
    def test_apply_writes_launcher_owned_main_agent_auth_profile(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            payload = json.loads(paths.main_agent_auth_profiles_file.read_text(encoding="utf-8"))
            self.assertIn("profiles", payload)
            self.assertIn("openai:launcher", payload["profiles"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_apply_preserves_unrelated_auth_profiles(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            paths.ensure_directories()
            paths.main_agent_auth_profiles_file.parent.mkdir(parents=True, exist_ok=True)
            paths.main_agent_auth_profiles_file.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "anthropic:manual": {
                                "provider": "anthropic",
                                "api_key": {"key": "sk-manual"},
                            }
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            payload = json.loads(paths.main_agent_auth_profiles_file.read_text(encoding="utf-8"))
            self.assertIn("anthropic:manual", payload["profiles"])
            self.assertIn("openai:launcher", payload["profiles"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_apply_skips_auth_profile_write_when_api_key_is_empty(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            bridge = ProviderBridge(paths)

            bridge.apply(
                make_config(
                    provider_id="dashscope",
                    provider_name="通义千问",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-max",
                ),
                SensitiveConfig(api_key=""),
            )

            self.assertFalse(paths.main_agent_auth_profiles_file.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
```

- [x] **Step 2: Run the provider-bridge tests to verify they fail**

Run: `python -m unittest tests.test_provider_bridge`

Expected: FAIL until merge-safe auth-store persistence is implemented.

- [x] **Step 3: Implement merge-safe auth profile writing**

Update `ProviderBridge.apply()` and helpers so they:

```python
    def _load_existing_auth_profiles(self) -> dict[str, object]:
        path = self.paths.main_agent_auth_profiles_file
        if not path.exists():
            return {"profiles": {}}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"profiles": {}}
        if not isinstance(payload, dict):
            return {"profiles": {}}
        profiles = payload.get("profiles")
        if not isinstance(profiles, dict):
            payload["profiles"] = {}
        return payload

    def _save_auth_profiles_document(self, launcher_document: dict[str, object]) -> None:
        current = self._load_existing_auth_profiles()
        current_profiles = current.setdefault("profiles", {})
        launcher_profiles = launcher_document.get("profiles", {})
        for profile_id, profile_value in launcher_profiles.items():
            current_profiles[profile_id] = profile_value
        self.paths.main_agent_auth_profiles_file.parent.mkdir(parents=True, exist_ok=True)
        self.paths.main_agent_auth_profiles_file.write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

Keep overwrite scope narrow:

- only update launcher-owned IDs
- preserve unknown IDs
- do not delete existing unrelated provider data

- [x] **Step 4: Run the provider-bridge tests again**

Run: `python -m unittest tests.test_provider_bridge`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add launcher/services/provider_bridge.py tests/test_provider_bridge.py
git commit -m "feat: persist launcher-managed main agent auth profiles"
```

### Task 3: Integrate Provider Bridge Into Controller Runtime Preparation

**Files:**
- Modify: `launcher/services/controller.py`
- Modify: `tests/test_launcher_controller.py`

- [x] **Step 1: Add failing controller integration tests**

Add coverage to `tests/test_launcher_controller.py`:

```python
    def test_configure_passes_provider_bridge_runtime_patch_into_prepare(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(paths, runtime_adapter=runtime_adapter, runtime_mode="openclaw")

            controller.configure(
                make_config(
                    provider_id="dashscope",
                    provider_name="通义千问",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-max",
                ),
                SensitiveConfig(api_key="sk-qwen"),
            )

            self.assertEqual(
                runtime_adapter.last_runtime_config_patch["agents"]["defaults"]["model"]["primary"],
                "qwen/qwen-max",
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_configure_writes_main_agent_auth_profiles_for_selected_provider(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(paths, runtime_adapter=runtime_adapter, runtime_mode="openclaw")

            controller.configure(
                make_config(
                    provider_id="openai",
                    provider_name="OpenAI",
                    base_url="https://api.openai.com/v1",
                    model="gpt-5.4",
                ),
                SensitiveConfig(api_key="sk-openai"),
            )

            payload = json.loads(paths.main_agent_auth_profiles_file.read_text(encoding="utf-8"))
            self.assertIn("openai:launcher", payload["profiles"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_channel_runtime_projection_and_provider_bridge_patch_are_merged(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            runtime_adapter = FakeRuntimeAdapter()
            controller = LauncherController(paths, runtime_adapter=runtime_adapter, runtime_mode="openclaw")
            controller.feishu_channel_service.save_config(
                FeishuChannelConfig(
                    app_id="cli_xxx",
                    app_secret="secret",
                    enabled=True,
                    bot_app_name="OpenClaw Bot",
                    last_validated_at=None,
                )
            )

            controller.configure(make_config(), SensitiveConfig(api_key="sk-qwen"))

            patch = runtime_adapter.last_runtime_config_patch
            self.assertEqual(patch["agents"]["defaults"]["model"]["primary"], "qwen/qwen-max")
            self.assertTrue(patch["channels"]["feishu"]["enabled"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
```

- [x] **Step 2: Run the focused controller tests**

Run: `python -m unittest tests.test_launcher_controller`

Expected: FAIL until controller wiring includes provider bridge output.

- [x] **Step 3: Wire the provider bridge into runtime projection**

Update `launcher/services/controller.py` so provider bridge output is included anywhere runtime projection happens:

```python
from launcher.services.provider_bridge import ProviderBridge


class LauncherController:
    def __init__(...):
        ...
        self.provider_bridge = ProviderBridge(paths)

    def configure(self, config: LauncherConfig, sensitive: SensitiveConfig) -> None:
        self.store.save(config, sensitive)
        provider_projection = self.provider_bridge.apply(config, sensitive)
        runtime_config_patch, runtime_env = self._channel_runtime_projection()
        runtime_config_patch = self._deep_merge(provider_projection.runtime_config_patch, runtime_config_patch)
        self._prepare_runtime_adapter(config, runtime_config_patch, runtime_env)
        self._prepared = True

    def _prepare_if_needed(self) -> None:
        if self._prepared or self.store.is_first_run():
            return
        config, sensitive = self.store.load()
        provider_projection = self.provider_bridge.apply(config, sensitive)
        runtime_config_patch, runtime_env = self._channel_runtime_projection()
        runtime_config_patch = self._deep_merge(provider_projection.runtime_config_patch, runtime_config_patch)
        self._prepare_runtime_adapter(config, runtime_config_patch, runtime_env)
        self._prepared = True
```

Mirror the same merge in `_reproject_channels_if_configured()`.

- [x] **Step 4: Run the controller tests again**

Run: `python -m unittest tests.test_launcher_controller`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add launcher/services/controller.py tests/test_launcher_controller.py
git commit -m "feat: bridge launcher providers into runtime preparation"
```

### Task 4: Add Minimal OpenAI And Anthropic Launcher Templates

**Files:**
- Create: `state/provider-templates/04-openai.json`
- Create: `state/provider-templates/05-anthropic.json`
- Modify: `tests/test_provider_templates.py`
- Modify: `tests/test_setup_wizard_flow.py`
- Modify: `tests/test_launcher_bootstrap.py`

- [x] **Step 1: Add failing template/flow tests**

Update `tests/test_provider_templates.py`:

```python
        self.assertEqual(
            [template.identifier for template in templates],
            ["dashscope", "deepseek", "openrouter", "openai", "anthropic", "custom"],
        )
        self.assertEqual(templates[3].base_url, "https://api.openai.com/v1")
        self.assertEqual(templates[4].base_url, "https://api.anthropic.com")
```

Update `tests/test_setup_wizard_flow.py` template factory:

```python
        ProviderTemplate("openai", "OpenAI", "https://api.openai.com/v1", "gpt-5.4", 40),
        ProviderTemplate("anthropic", "Anthropic", "https://api.anthropic.com", "claude-sonnet-4-6", 50),
```

Add one selection assertion:

```python
    def test_builds_openai_configuration_from_selected_template(self) -> None:
        session = SetupWizardSession(make_templates())
        session.selected_provider_id = "openai"
        session.api_key = "sk-openai"

        config, sensitive = session.build_configuration()

        self.assertEqual(config.provider_id, "openai")
        self.assertEqual(config.model, "gpt-5.4")
        self.assertEqual(sensitive.api_key, "sk-openai")
```

Update `tests/test_launcher_bootstrap.py` wizard-step fixture if it asserts template list order or default copy.

- [x] **Step 2: Run the provider-template and wizard tests**

Run: `python -m unittest tests.test_provider_templates tests.test_setup_wizard_flow tests.test_launcher_bootstrap`

Expected: FAIL until the template files are added and expected lists are updated.

- [x] **Step 3: Add the new built-in templates**

Create `state/provider-templates/04-openai.json`:

```json
{
  "id": "openai",
  "displayName": "OpenAI",
  "baseUrl": "https://api.openai.com/v1",
  "defaultModel": "gpt-5.4",
  "order": 40
}
```

Create `state/provider-templates/05-anthropic.json`:

```json
{
  "id": "anthropic",
  "displayName": "Anthropic",
  "baseUrl": "https://api.anthropic.com",
  "defaultModel": "claude-sonnet-4-6",
  "order": 50
}
```

Keep the UI unchanged beyond the combo list contents. Do not redesign the wizard.

- [x] **Step 4: Run the template and wizard tests again**

Run: `python -m unittest tests.test_provider_templates tests.test_setup_wizard_flow tests.test_launcher_bootstrap`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add state/provider-templates/04-openai.json state/provider-templates/05-anthropic.json tests/test_provider_templates.py tests/test_setup_wizard_flow.py tests/test_launcher_bootstrap.py
git commit -m "feat: add openai and anthropic launcher templates"
```

### Task 5: Full Verification And Package Rebuild

**Files:**
- Modify if verification exposes edge cases: `launcher/services/provider_bridge.py`, `launcher/services/controller.py`, associated tests

- [x] **Step 1: Run the full focused verification slice**

Run: `python -m unittest tests.test_provider_bridge tests.test_core_services tests.test_launcher_controller tests.test_provider_templates tests.test_setup_wizard_flow tests.test_launcher_bootstrap`

Expected: PASS

- [x] **Step 2: Run the full repository test suite**

Run: `python -m unittest discover -s tests`

Expected: PASS

- [x] **Step 3: Rebuild the packaged launcher and release assets**

Run: `.\scripts\build-release-assets.ps1`

Expected: build succeeds and refreshes both:

- `dist\OpenClaw-Portable\`
- `dist\release\OpenClaw-Portable-v2026.04.6.zip`

- [x] **Step 4: Verify the new package keeps runtime auth bridge expectations**

Run:

```powershell
@(
  'dist\OpenClaw-Portable\state\agents\main\agent\auth-profiles.json',
  'dist\OpenClaw-Portable\state\provider-templates\04-openai.json',
  'dist\OpenClaw-Portable\state\provider-templates\05-anthropic.json'
) | ForEach-Object { "$_`t$(Test-Path $_)" }
```

Expected:

- provider template files exist
- `auth-profiles.json` will exist after launcher configuration flow executes in a real run

- [x] **Step 5: Re-run delivery-flow verification**

Run: `python scripts\verify-delivery-flow.py --package-root dist\OpenClaw-Portable --release-dir dist\release --cold-runs 1 --restart-runs 1 --timeout-seconds 90 --output tmp\delivery-flow-gate-provider-bridge.json`

Expected: local package audit, release assets, and runtime stability still PASS; only external evidence remains pending.

- [x] **Step 6: Commit**

```bash
git add launcher/services/provider_bridge.py launcher/services/controller.py launcher/core/paths.py state/provider-templates/04-openai.json state/provider-templates/05-anthropic.json tests/test_provider_bridge.py tests/test_launcher_controller.py tests/test_provider_templates.py tests/test_setup_wizard_flow.py tests/test_launcher_bootstrap.py docs/superpowers/plans/2026-04-25-provider-bridge-runtime-auth.md
git commit -m "feat: bridge launcher provider config into runtime auth"
```

### Self-Review Notes

- Spec coverage:
  - provider detection: Task 1
  - runtime patch + auth store generation: Tasks 1-2
  - controller integration points: Task 3
  - OpenAI / Anthropic launcher usability: Task 4
  - verification and rebuild: Task 5
- Placeholder scan:
  - no `TODO` / `TBD`
  - all tasks include exact file paths and commands
- Type consistency:
  - plan assumes `ProviderBridge`, `ProviderBridgeProjection`, `paths.main_agent_auth_profiles_file`, and controller-owned `provider_bridge`
  - later tasks reuse those same names consistently
