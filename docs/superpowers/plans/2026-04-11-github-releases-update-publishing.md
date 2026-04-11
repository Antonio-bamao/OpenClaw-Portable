# GitHub Releases Update Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate GitHub Releases-ready zip and `update.json` assets for the portable package, and point the app's default update feed to the repository's latest release asset URL.

**Architecture:** Keep `build-launcher.ps1` focused on producing `dist/OpenClaw-Portable/`, then add a thin release-assets layer on top that zips the package and emits `update.json`. Put naming and metadata logic in a small Python module so unit tests cover the release URL, asset naming, and JSON generation without depending on PowerShell.

**Tech Stack:** Python 3 standard library, PowerShell, `unittest`, existing launcher services.

---

### Task 1: Add failing tests for GitHub Releases metadata and feed defaults

**Files:**
- Modify: `tests/test_update_feed.py`
- Create: `tests/test_release_assets.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_default_update_feed_url_points_to_latest_release_update_json(self) -> None:
    self.assertEqual(
        DEFAULT_UPDATE_FEED_URL,
        "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json",
    )

def test_build_release_asset_name_uses_version(self) -> None:
    self.assertEqual(build_release_asset_name("v2026.04.2"), "OpenClaw-Portable-v2026.04.2.zip")

def test_build_release_package_url_targets_release_tag_asset(self) -> None:
    self.assertEqual(
        build_release_package_url("Antonio-bamao/OpenClaw-Portable", "v2026.04.2"),
        "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/download/v2026.04.2/OpenClaw-Portable-v2026.04.2.zip",
    )
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_feed tests.test_release_assets -v`
Expected: FAIL because the GitHub Releases defaults and release-assets helper module do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
DEFAULT_UPDATE_FEED_URL = "https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json"

def build_release_asset_name(version: str) -> str:
    return f"OpenClaw-Portable-{version}.zip"

def build_release_package_url(repository: str, version: str) -> str:
    asset_name = build_release_asset_name(version)
    return f"https://github.com/{repository}/releases/download/{version}/{asset_name}"
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_feed tests.test_release_assets -v`
Expected: PASS

### Task 2: Add failing tests for release asset packaging and update.json generation

**Files:**
- Modify: `tests/test_release_assets.py`
- Create: `launcher/services/release_assets.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_create_release_zip_preserves_portable_root_directory(self) -> None:
    archive_path = create_release_zip(package_root, output_dir)
    with zipfile.ZipFile(archive_path, "r") as archive:
        self.assertIn("OpenClaw-Portable/version.json", archive.namelist())

def test_write_release_update_json_writes_expected_document(self) -> None:
    output_path = write_release_update_json(
        version="v2026.04.2",
        repository="Antonio-bamao/OpenClaw-Portable",
        notes=["note a"],
        output_path=output_path,
    )
    document = json.loads(output_path.read_text(encoding="utf-8"))
    self.assertEqual(document["version"], "v2026.04.2")
    self.assertEqual(document["notes"], ["note a"])
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_release_assets -v`
Expected: FAIL because zip packaging and update.json writing are not implemented yet.

- [ ] **Step 3: Write minimal implementation**

```python
def create_release_zip(package_root: Path, output_dir: Path) -> Path:
    ...

def write_release_update_json(*, version: str, repository: str, notes: list[str], output_path: Path) -> Path:
    ...
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_release_assets -v`
Expected: PASS

### Task 3: Add release asset build scripts and keep build responsibilities separated

**Files:**
- Create: `scripts/build-release-assets.py`
- Create: `scripts/build-release-assets.ps1`
- Modify: `scripts/build-launcher.ps1`

- [ ] **Step 1: Add a failing script-level test for the Python release builder**

```python
def test_build_release_assets_creates_zip_and_update_json(self) -> None:
    build_release_assets(package_root=package_root, output_dir=output_dir, repository="Antonio-bamao/OpenClaw-Portable", notes=["note a"])
    self.assertTrue((output_dir / "OpenClaw-Portable-v2026.04.2.zip").exists())
    self.assertTrue((output_dir / "update.json").exists())
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_release_assets -v`
Expected: FAIL because the release-assets orchestration function/script entry point does not exist yet.

- [ ] **Step 3: Implement the Python builder and PowerShell wrapper**

```python
def build_release_assets(*, package_root: Path, output_dir: Path, repository: str, notes: list[str]) -> tuple[Path, Path]:
    ...
```

```powershell
& $PythonExe (Join-Path $root "scripts\\build-release-assets.py") `
  --package-root $portableDist `
  --output-dir (Join-Path $root "dist\\release") `
  --repository "Antonio-bamao/OpenClaw-Portable"
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_release_assets -v`
Expected: PASS

### Task 4: Wire the GitHub Releases default feed and verify regressions

**Files:**
- Modify: `launcher/services/update_feed.py`
- Modify: `tests/test_online_update.py`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_update_feed tests.test_release_assets tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 2: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: FAIL only on the pre-existing `PySide6` import errors in UI-oriented modules.

### Task 5: Update project context and validate it

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/decisions.md`
- Modify: `.context/work-log.md`

- [ ] **Step 1: Record the GitHub Releases publishing rule**

```text
Document that the portable package now treats GitHub Releases as the default update hosting target, builds a release zip plus update.json, and resolves the default feed from the repository's latest release asset URL.
```

- [ ] **Step 2: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
