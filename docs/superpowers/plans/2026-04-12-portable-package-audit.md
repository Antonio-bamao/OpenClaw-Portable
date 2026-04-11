# Portable Package Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only portable package audit tool for package size, file count, required paths, largest directories, and U-disk write-risk hints.

**Architecture:** Add a focused service module that scans a package directory and returns dataclasses, plus a thin JSON CLI script. Keep the tool independent from release publishing so it cannot bump versions or upload assets.

**Tech Stack:** Python 3, `unittest`, standard-library `argparse`, `dataclasses`, `json`, `pathlib`.

---

### Task 1: Service And CLI

**Files:**
- Create: `tests/test_portable_audit.py`
- Create: `launcher/services/portable_audit.py`
- Create: `scripts/audit-portable-package.py`

- [ ] **Step 1: Write failing service tests**

Create `tests/test_portable_audit.py` with tests that build a fake package tree, call `audit_portable_package`, and assert total bytes, total files, missing paths, largest directories, write-risk directories, and low-space warnings.

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests.test_portable_audit -v`
Expected: import failure for `launcher.services.portable_audit`.

- [ ] **Step 3: Implement service**

Create `launcher/services/portable_audit.py` with `PortablePackageAuditResult`, `PortableDirectorySummary`, `audit_portable_package`, and JSON conversion helpers.

- [ ] **Step 4: Add and test CLI**

Add `scripts/audit-portable-package.py` and extend `tests/test_portable_audit.py` with a subprocess CLI test using the fake package tree.

- [ ] **Step 5: Run targeted and full tests**

Run: `python -m unittest tests.test_portable_audit -v`
Run: `python -m unittest discover -s tests`

- [ ] **Step 6: Update context and commit**

Update `.context/work-log.md`, `.context/current-status.md`, and `.context/task-breakdown.md`. Run `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`, then commit the change.
