# Restore Update Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a launcher flow that restores a previous portable distribution snapshot from `state/backups/updates/` without overwriting `state/`, while preserving rollback safety.

**Architecture:** Add a restore service parallel to `LocalUpdateImportService`, wire it through `LauncherController`, then expose it from the main window with a confirmation dialog and backup-directory picker. The implementation should reuse the same replace-only distribution entry set and the same rollback philosophy as local update import.

**Tech Stack:** Python 3, PySide6, `unittest`, existing launcher services/controllers/UI.

---

### Task 1: Add failing restore service tests

**Files:**
- Modify: `tests/test_local_update.py`
- Test: `tests/test_local_update.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_restores_distribution_content_from_backup_without_overwriting_state(self) -> None:
    result = LocalUpdateImportService(paths).restore_backup(backup_root)
    self.assertEqual(result.restored_version, "v1")

def test_restore_rolls_back_when_copy_fails_mid_restore(self) -> None:
    with self.assertRaisesRegex(RuntimeError, "simulated restore failure"):
        FailingRestoreUpdateBackupService(paths).restore_backup(backup_root)

def test_restore_requires_at_least_one_distribution_entry(self) -> None:
    with self.assertRaisesRegex(FileNotFoundError, "备份目录中没有可恢复的分发内容"):
        LocalUpdateImportService(paths).restore_backup(empty_backup_root)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_local_update -v`
Expected: FAIL because `restore_backup` and restore result fields do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class RestoreUpdateBackupResult:
    restored_version: str
    backup_dir: Path
    restored_entries: list[str]
    source_backup_dir: Path

class RestoreUpdateBackupService:
    def restore_backup(self, backup_root: Path) -> RestoreUpdateBackupResult:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_local_update -v`
Expected: PASS

### Task 2: Wire controller and app flow with tests first

**Files:**
- Modify: `launcher/services/controller.py`
- Modify: `launcher/app.py`
- Modify: `tests/test_launcher_app.py`
- Create or Modify: `tests/test_launcher_controller.py`

- [ ] **Step 1: Write the failing controller/app tests**

```python
def test_restore_update_backup_stops_runtime_and_resets_prepared(self) -> None:
    version = controller.restore_update_backup(Path("C:/tmp/backup"))
    self.assertEqual(version, "v1")

def test_handle_restore_update_backup_shows_restart_prompt_after_success(self) -> None:
    application._handle_restore_update_backup()
    self.assertIn("v1", info_messages[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_controller -v`
Expected: FAIL because restore methods/handlers are missing.

- [ ] **Step 3: Write minimal implementation**

```python
def restore_update_backup(self, backup_root: Path) -> str:
    self.runtime_adapter.stop()
    result = self.restore_update_backup_service.restore_backup(backup_root)
    self._prepared = False
    return result.restored_version
```

```python
def _handle_restore_update_backup(self) -> None:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_controller -v`
Expected: PASS

### Task 3: Expose the new main-window action and verify UI text

**Files:**
- Modify: `launcher/ui/main_window.py`
- Modify: `tests/test_launcher_app.py`

- [ ] **Step 1: Write the failing UI smoke expectation**

```python
self.assertIn("恢复更新备份", window.secondary_action_texts())
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python -m unittest tests.test_launcher_app -v`
Expected: FAIL because the button text/handler is not present.

- [ ] **Step 3: Write minimal implementation**

```python
self.restore_update_backup_button = make_button("恢复更新备份")
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `python -m unittest tests.test_launcher_app -v`
Expected: PASS

### Task 4: Verify broader regression safety and update project context

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`
- Modify: `.context/decisions.md`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_local_update tests.test_launcher_app tests.test_launcher_controller tests.test_launcher_bootstrap -v`
Expected: PASS

- [ ] **Step 2: Run the full test suite**

Run: `python -m unittest discover -s tests`
Expected: PASS

- [ ] **Step 3: Update project context files**

```text
Record the new restore-from-backup capability, its safety boundary, and the next recommended step.
```

- [ ] **Step 4: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
