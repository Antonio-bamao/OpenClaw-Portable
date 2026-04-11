# Update Manifest Hash Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `update-manifest.json` generation plus SHA-256 validation so local update packages are only imported when their contents are complete and untampered.

**Architecture:** Introduce a shared Python hashing/manifest module that both the build output and the local update import flow use. Generate the manifest at the end of `build-launcher.ps1`, then require and verify it before any update backup or file replacement occurs.

**Tech Stack:** Python 3, PowerShell build script, `unittest`, existing local update flow.

---

### Task 1: Add failing tests for manifest hashing and validation

**Files:**
- Create or Modify: `tests/test_update_manifest.py`
- Modify: `tests/test_local_update.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_generates_manifest_with_expected_entries(self) -> None:
    manifest = build_update_manifest(package_root)
    self.assertIn("runtime", manifest["entries"])

def test_rejects_update_package_without_manifest(self) -> None:
    with self.assertRaisesRegex(FileNotFoundError, "update-manifest.json"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_rejects_update_package_when_manifest_hash_does_not_match(self) -> None:
    with self.assertRaisesRegex(ValueError, "完整性校验失败"):
        LocalUpdateImportService(paths).import_package(source_root)

def test_rejects_update_package_when_manifest_version_mismatches_version_json(self) -> None:
    with self.assertRaisesRegex(ValueError, "版本信息与完整性清单不一致"):
        LocalUpdateImportService(paths).import_package(source_root)
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_manifest tests.test_local_update -v`
Expected: FAIL because manifest generation/validation does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def build_update_manifest(package_root: Path) -> dict[str, object]:
    ...

def validate_update_manifest(package_root: Path, expected_version: str) -> None:
    ...
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_manifest tests.test_local_update -v`
Expected: PASS

### Task 2: Hook manifest generation into the portable build output

**Files:**
- Create: `launcher/services/update_manifest.py`
- Modify: `scripts/build-launcher.ps1`

- [ ] **Step 1: Add or reuse tests proving the manifest module output is correct**

```python
def test_directory_hash_changes_when_file_content_changes(self) -> None:
    ...
```

- [ ] **Step 2: Wire the build script to generate `update-manifest.json`**

Run after runtime pruning:
```powershell
& $PythonExe (Join-Path $root "scripts\\generate-update-manifest.py") --package-root $portableDist
```

- [ ] **Step 3: Run module tests again**

Run: `python -m unittest tests.test_update_manifest -v`
Expected: PASS

### Task 3: Verify broader regressions and update project context

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`
- Modify: `.context/decisions.md`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_update_manifest tests.test_local_update tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 2: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: PASS except for pre-existing `PySide6` import failures in UI-oriented modules.

- [ ] **Step 3: Update project context**

```text
Record that local update import now requires update-manifest SHA-256 validation and that build outputs generate the manifest automatically.
```

- [ ] **Step 4: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
