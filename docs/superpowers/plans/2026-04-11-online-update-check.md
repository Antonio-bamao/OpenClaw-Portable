# Online Update Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative online update flow that checks a static JSON endpoint, downloads a zip package to temp storage, extracts it, and hands the extracted portable package to the existing local update import pipeline.

**Architecture:** Introduce a focused service module for update metadata fetch + package download/extract, keep the existing `LocalUpdateImportService` as the only component allowed to replace files, and wire the main-window action through `LauncherController` and `OpenClawLauncherApplication`. The online path should only prepare a local package directory; version checks, manifest checks, backup, replacement, and rollback remain in the existing import flow.

**Tech Stack:** Python 3 standard library (`json`, `urllib`, `zipfile`, `tempfile`/`pathlib`), PowerShell-free runtime logic, `unittest`, existing launcher services/controller/app layers.

---

### Task 1: Add failing tests for metadata fetch and download/extract behavior

**Files:**
- Create: `tests/test_online_update.py`
- Modify: `tests/test_launcher_controller.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_check_update_returns_update_available_when_remote_version_is_newer(self) -> None:
    service = OnlineUpdateService(paths, update_feed_url="https://example.com/update.json", fetch_text=fake_fetch_text)
    result = service.check_for_updates("v2026.04.1")
    self.assertTrue(result.update_available)
    self.assertEqual(result.latest_version, "v2026.04.2")

def test_check_update_rejects_invalid_update_json(self) -> None:
    with self.assertRaisesRegex(ValueError, "更新信息格式错误"):
        service.check_for_updates("v2026.04.1")

def test_download_update_package_downloads_and_extracts_zip_to_temp_package_dir(self) -> None:
    package_dir = service.download_update_package(metadata)
    self.assertTrue((package_dir / "version.json").exists())

def test_controller_online_update_imports_downloaded_package_and_resets_prepared_state(self) -> None:
    imported_version = controller.check_and_import_update()
    self.assertEqual(imported_version, "v2026.04.2")
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m unittest tests.test_online_update tests.test_launcher_controller -v`
Expected: FAIL because the online update service/controller methods do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    latest_version: str
    notes: list[str]
    package_url: str

class OnlineUpdateService:
    def check_for_updates(self, current_version: str) -> UpdateCheckResult:
        ...

    def download_update_package(self, metadata: UpdateCheckResult) -> Path:
        ...
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `python -m unittest tests.test_online_update tests.test_launcher_controller -v`
Expected: PASS

### Task 2: Wire the main application and window action with tests first where possible

**Files:**
- Modify: `launcher/services/controller.py`
- Modify: `launcher/app.py`
- Modify: `launcher/ui/main_window.py`
- Modify: `tests/test_launcher_app.py`
- Modify: `tests/test_launcher_bootstrap.py`

- [ ] **Step 1: Write the failing orchestration/UI smoke tests**

```python
def test_handle_check_update_shows_latest_message_when_no_update_is_available(self) -> None:
    application._handle_check_update()
    self.assertIn("已经是最新版本", info_messages[0])

def test_handle_check_update_downloads_and_imports_after_confirmation(self) -> None:
    application._handle_check_update()
    self.assertIn("v2026.04.2", info_messages[0])

def test_builds_main_window_with_check_update_action(self) -> None:
    self.assertIn("检查更新", window.secondary_action_texts())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_bootstrap -v`
Expected: In this environment these modules currently fail to import because `PySide6` is missing; still add the tests now so they become runnable once the dependency is available.

- [ ] **Step 3: Write minimal implementation**

```python
def check_and_import_update(self) -> str | None:
    ...

def _handle_check_update(self) -> None:
    ...
```

```python
self.check_update_button = make_button("检查更新")
```

- [ ] **Step 4: Re-run whatever is available**

Run: `python -m unittest tests.test_online_update tests.test_launcher_controller -v`
Expected: PASS

### Task 3: Verify regression safety and update project context

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`
- Modify: `.context/decisions.md`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 2: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: PASS except for the pre-existing `PySide6` import failures in UI-oriented modules.

- [ ] **Step 3: Update project context**

```text
Record that online update now checks a static JSON endpoint, downloads a zip package to temp storage, and then reuses the existing local import pipeline.
```

- [ ] **Step 4: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
