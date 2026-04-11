# Local Update Package Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strict structure and version validation to the local update import flow so only genuinely newer update packages can be imported.

**Architecture:** Keep validation inside `launcher/services/local_update.py` so the import and restore rules stay co-located. Validate package structure and compare current/incoming versions before creating a backup or replacing any files.

**Tech Stack:** Python 3, `unittest`, existing launcher service/controller/application flow.

---

### Task 1: Add failing validation tests around local update import

**Files:**
- Modify: `tests/test_local_update.py`
- Test: `tests/test_local_update.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_rejects_package_with_invalid_version_json(self) -> None:
    with self.assertRaisesRegex(ValueError, "不是合法 JSON"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_rejects_package_without_distribution_entries(self) -> None:
    with self.assertRaisesRegex(FileNotFoundError, "没有可导入的程序文件"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_rejects_same_version_package(self) -> None:
    with self.assertRaisesRegex(ValueError, "无需重复导入"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_rejects_older_version_package_and_guides_restore_flow(self) -> None:
    with self.assertRaisesRegex(ValueError, "恢复更新备份"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_release_version_is_newer_than_same_dev_version(self) -> None:
    result = LocalUpdateImportService(paths).import_package(source_root)
    self.assertEqual(result.imported_version, "v2026.04.1")
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m unittest tests.test_local_update -v`
Expected: FAIL because validation helpers and version comparison rules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def _validate_import_source(self, source_root: Path) -> tuple[Path, str]:
    ...

def _compare_versions(self, left: str, right: str) -> int:
    ...
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `python -m unittest tests.test_local_update -v`
Expected: PASS

### Task 2: Verify higher-level flow remains stable

**Files:**
- Modify: `tests/test_launcher_controller.py` if needed
- Modify: `tests/test_runtime_errors.py` only if new user-facing wording needs explicit regression coverage

- [ ] **Step 1: Add any failing regression tests only if behavior changed above the service layer**

```python
# Only add tests if controller/app behavior changes beyond service-level validation.
```

- [ ] **Step 2: Run the scoped regression suite**

Run: `python -m unittest tests.test_local_update tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 3: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: PASS except for pre-existing `PySide6` import failures in UI-oriented modules.

### Task 3: Update project context and validate it

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`
- Modify: `.context/decisions.md`

- [ ] **Step 1: Record the new validation rule and remaining next step**

```text
Document that local update import is now a strict upgrade-only path and that downgrade guidance points to the restore-backup flow.
```

- [ ] **Step 2: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
