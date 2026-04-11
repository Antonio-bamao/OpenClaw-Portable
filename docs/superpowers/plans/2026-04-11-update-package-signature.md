# Update Package Signature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Ed25519 signing for `update-manifest.json` so release packages include a trusted publisher signature and update import rejects unsigned or forged packages before any file replacement begins.

**Architecture:** Introduce a small shared signature module backed by `PyNaCl`. Release-side scripts generate keypairs and sign `update-manifest.json` into `update-signature.json`, while `LocalUpdateImportService` verifies that signature before running the existing manifest and replacement pipeline.

**Tech Stack:** Python 3, `PyNaCl`, PowerShell, `unittest`, existing launcher services and release-asset scripts.

---

### Task 1: Add the crypto dependency and failing signature unit tests

**Files:**
- Modify: `requirements.txt`
- Create: `tests/test_update_signature.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_generate_keypair_returns_base64_private_and_public_keys(self) -> None:
    private_key, public_key = generate_update_signing_keypair()
    self.assertTrue(private_key)
    self.assertTrue(public_key)

def test_sign_and_verify_manifest_bytes_round_trip(self) -> None:
    private_key, public_key = generate_update_signing_keypair()
    signature_document = build_update_signature_document(manifest_bytes=b"{}", private_key_b64=private_key)
    verify_update_signature_document(
        manifest_bytes=b"{}",
        signature_document=signature_document,
        expected_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
        public_key_b64=public_key,
    )
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_signature -v`
Expected: FAIL because the signature module and dependency do not exist yet.

- [ ] **Step 3: Add the dependency and minimal signature module**

```text
PyNaCl>=1.5,<2.0
```

```python
def generate_update_signing_keypair() -> tuple[str, str]:
    ...
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_signature -v`
Expected: PASS

### Task 2: Add failing verification tests to local update import

**Files:**
- Modify: `tests/test_local_update.py`
- Modify: `launcher/services/local_update.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_rejects_update_package_without_signature(self) -> None:
    ...

def test_rejects_update_package_when_signature_does_not_match_manifest(self) -> None:
    ...

def test_imports_signed_package_when_signature_and_manifest_are_valid(self) -> None:
    ...
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_signature tests.test_local_update -v`
Expected: FAIL because signature verification is not integrated into the import pipeline yet.

- [ ] **Step 3: Implement minimal verification in the import flow**

```python
verify_update_signature(
    source_root,
    expected_key_id=DEFAULT_UPDATE_SIGNING_KEY_ID,
    public_key_b64=DEFAULT_UPDATE_SIGNING_PUBLIC_KEY,
)
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_signature tests.test_local_update -v`
Expected: PASS

### Task 3: Add release-side signing and keypair generation scripts

**Files:**
- Create: `scripts/generate-update-signing-keypair.py`
- Create: `scripts/sign-update-manifest.py`
- Modify: `scripts/build-release-assets.ps1`
- Modify: `tests/test_release_assets.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing release-side tests**

```python
def test_write_update_signature_creates_signature_file(self) -> None:
    ...

def test_build_release_assets_zip_contains_update_signature_file(self) -> None:
    ...
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_signature tests.test_release_assets -v`
Expected: FAIL because signing output is not generated yet.

- [ ] **Step 3: Implement signing scripts and release integration**

```powershell
& $PythonExe (Join-Path $root "scripts\\sign-update-manifest.py") `
  --package-root $packageRoot `
  --private-key-path (Join-Path $root ".local\\update-signing-private-key.txt")
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_signature tests.test_release_assets -v`
Expected: PASS

### Task 4: Update project context and verify the available test envelope

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/decisions.md`
- Modify: `.context/work-log.md`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_update_signature tests.test_release_assets tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 2: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: FAIL only on the pre-existing `PySide6` import errors in UI-oriented modules.

- [ ] **Step 3: Record the signature rule and validate context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
