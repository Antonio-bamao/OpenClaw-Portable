# OpenClaw Simple Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fragile launcher startup path with a minimal OpenClaw boot flow that only depends on the local gateway becoming reachable.

**Architecture:** Keep the existing PySide launcher shell, config projection, and packaged runtime. Simplify runtime start to `spawn node + openclaw.mjs + poll local gateway`, then remove startup-critical Feishu probing from the controller so optional channel checks cannot invalidate a successful boot.

**Tech Stack:** Python 3.12, PySide6 launcher, bundled Node/OpenClaw runtime, `unittest`

---

### Task 1: Lock The Minimal Runtime Startup Contract

**Files:**
- Modify: `tests/test_openclaw_runtime_adapter.py`
- Modify: `launcher/runtime/openclaw_runtime.py`

- [ ] **Step 1: Write failing tests for the simpler readiness model**

Add coverage for:
- startup readiness succeeding when the gateway becomes reachable without any extra channel logic
- startup failure when the process exits before readiness
- Windows launch still hiding the child console

- [ ] **Step 2: Run the focused runtime adapter tests to verify the new assertions fail when appropriate**

Run: `python -m unittest tests.test_openclaw_runtime_adapter`

Expected: at least one failure if the new behavior is not implemented yet.

- [ ] **Step 3: Refactor runtime startup to match the new contract**

Update `OpenClawRuntimeAdapter` so that:
- `start()` only launches the Node process and waits for gateway reachability
- readiness polling is based on direct gateway health/reachability
- process-exit-before-ready remains a hard failure
- Windows launch uses hidden-console creation flags

- [ ] **Step 4: Run the runtime adapter tests again**

Run: `python -m unittest tests.test_openclaw_runtime_adapter`

Expected: PASS

### Task 2: Remove Startup-Critical Feishu Probe Coupling

**Files:**
- Modify: `tests/test_launcher_controller.py`
- Modify: `tests/test_feishu_channel_service.py`
- Modify: `launcher/services/controller.py`
- Modify: `launcher/services/feishu_channel.py` only if status semantics need minimal adjustment

- [ ] **Step 1: Write failing controller/service tests for probe-free startup**

Add coverage for:
- runtime `running` status being treated as started even when no Feishu live probe ran
- optional probe failures not being part of startup success criteria
- channel status falling back to pending/connected semantics without turning runtime startup into an error

- [ ] **Step 2: Run the focused controller/channel tests**

Run: `python -m unittest tests.test_launcher_controller tests.test_feishu_channel_service`

Expected: FAIL until controller semantics are updated.

- [ ] **Step 3: Simplify the controller refresh path**

Change the controller so that:
- startup success depends on runtime status/reachability only
- Feishu live probe is not run from the startup-critical main view refresh path
- optional channel inspection can happen later without flipping a healthy runtime into a startup failure

- [ ] **Step 4: Run the controller/channel tests again**

Run: `python -m unittest tests.test_launcher_controller tests.test_feishu_channel_service`

Expected: PASS

### Task 3: Align Error Copy With Real Runtime State

**Files:**
- Modify: `launcher/services/runtime_errors.py`
- Modify: `tests/test_launcher_app.py` or another launcher-facing test file if needed

- [ ] **Step 1: Add failing tests or assertions for runtime error wording if coverage is missing**

Cover:
- process exited before ready
- startup timeout
- successful startup not being mislabeled as "提前退出"

- [ ] **Step 2: Run the affected launcher/runtime error tests**

Run: `python -m unittest tests.test_launcher_app`

Expected: FAIL if new wording/behavior is not yet implemented.

- [ ] **Step 3: Adjust error formatting to reflect true runtime state**

Keep user-facing copy short and specific to:
- missing runtime files
- startup timeout
- process exited before gateway readiness

- [ ] **Step 4: Re-run the launcher-facing tests**

Run: `python -m unittest tests.test_launcher_app`

Expected: PASS

### Task 4: Verify The Full Path And Rebuild

**Files:**
- Modify if needed after verification: same files above

- [ ] **Step 1: Run the full targeted verification suite**

Run: `python -m unittest tests.test_openclaw_runtime_adapter tests.test_launcher_controller tests.test_feishu_channel_service tests.test_launcher_app`

Expected: PASS

- [ ] **Step 2: Rebuild the packaged launcher**

Run: `.\\scripts\\build-launcher.ps1`

Expected: build succeeds and updates `dist/OpenClaw-Portable/OpenClawLauncher.exe`

- [ ] **Step 3: Spot-check packaged artifact metadata**

Run: `Get-Item 'dist\\OpenClaw-Portable\\OpenClawLauncher.exe' | Select-Object FullName,Length,LastWriteTime`

Expected: file exists with a fresh timestamp
