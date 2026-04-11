# Update Signing Key Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-public-key verification for update package signatures so signing keys can be rotated safely.

**Architecture:** Extend `launcher/services/update_signature.py` to verify against a trusted `{keyId: publicKey}` map while preserving the existing single-key parameters. Update `LocalUpdateImportService` to carry that map into import validation.

**Tech Stack:** Python 3, PyNaCl, unittest.

---

### Task 1: Add failing tests for trusted key maps

**Files:**
- Modify: `tests/test_update_signature.py`
- Modify: `tests/test_local_update.py`

- [ ] **Step 1: Add signature-module tests**

Add tests that sign a manifest with a secondary `keyId` and verify it through `trusted_public_keys`.

- [ ] **Step 2: Add local-update import test**

Add a test package signed with a secondary key and configure `LocalUpdateImportService` with both public keys.

- [ ] **Step 3: Run focused tests**

Run: `python -m unittest tests.test_update_signature tests.test_local_update -v`
Expected: fail because trusted key maps are not implemented yet.

### Task 2: Implement trusted key map verification

**Files:**
- Modify: `launcher/services/update_signature.py`
- Modify: `launcher/services/local_update.py`

- [ ] **Step 1: Add `DEFAULT_UPDATE_SIGNING_PUBLIC_KEYS`**

Expose the default trusted key map using the current key id and public key.

- [ ] **Step 2: Select public key by signature `keyId`**

When `trusted_public_keys` is supplied, look up the signature document's `keyId` and verify with that public key.

- [ ] **Step 3: Preserve single-key compatibility**

If no trusted map is supplied, keep using `expected_key_id` and `public_key_b64`.

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_update_signature tests.test_local_update -v`
Expected: pass.

### Task 3: Verify and record context

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/decisions.md`
- Modify: `.context/work-log.md`

- [ ] **Step 1: Run scoped regression**

Run: `python -m unittest tests.test_update_signature tests.test_release_assets tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v`
Expected: pass.

- [ ] **Step 2: Run context validation**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`.
