# WeChat / QQ Launcher Status Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the launcher's WeChat and QQ cards explain the user's current stage, expose local setup help, and refresh WeChat login progress without guessing.

**Architecture:** Keep the current card layout and service boundaries. Extend the social channel service with richer state labels, add local help pages under `assets/guide/`, and wire WeChat/QQ help buttons plus refresh hooks through the existing app/UI flow.

**Tech Stack:** Python 3.12, PySide6, unittest, packaged HTML help pages

---

### Task 1: Add failing tests for WeChat / QQ help and status mapping

**Files:**
- Modify: `tests/test_launcher_bootstrap.py`
- Modify: `tests/test_launcher_app.py`

- [ ] **Step 1: Write the failing bootstrap/UI tests**

Add assertions for:

```python
self.assertEqual(window.open_wechat_help_button.text(), "接入帮助")
self.assertEqual(window.open_qq_help_button.text(), "接入帮助")
self.assertIn("QQ Bot 扩展", window.qq_status_detail_label.text())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_bootstrap -v`
Expected: FAIL because the WeChat/QQ help buttons and refined QQ status mapping are not implemented yet.

- [ ] **Step 3: Write the failing app tests**

Add assertions for:

```python
application._handle_open_wechat_help()
application._handle_open_qq_help()
```

with patched browser-opening behavior and a fake window/controller.

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_app -v`
Expected: FAIL because the help handlers do not exist yet.

- [ ] **Step 5: Commit**

```bash
git add tests/test_launcher_bootstrap.py tests/test_launcher_app.py
git commit -m "test: cover wechat qq help entrypoints"
```

### Task 2: Add packaged WeChat / QQ help pages

**Files:**
- Create: `assets/guide/setup-wechat.html`
- Create: `assets/guide/setup-qq.html`
- Modify: `tests/test_launcher_bootstrap.py`

- [ ] **Step 1: Write the failing packaged-help assertions**

Add assertions like:

```python
self.assertTrue((Path.cwd() / "assets" / "guide" / "setup-wechat.html").exists())
self.assertTrue((Path.cwd() / "assets" / "guide" / "setup-qq.html").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_bootstrap.LauncherUiSmokeTests -v`
Expected: FAIL because the help pages do not exist yet.

- [ ] **Step 3: Add the two HTML help pages**

Create short packaged help pages in Chinese with:

- required setup inputs
- what each launcher button does
- common failures
- next step after success

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_launcher_bootstrap.LauncherUiSmokeTests -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add assets/guide/setup-wechat.html assets/guide/setup-qq.html tests/test_launcher_bootstrap.py
git commit -m "docs: add wechat qq setup help pages"
```

### Task 3: Wire WeChat / QQ help buttons in the launcher UI and app

**Files:**
- Modify: `launcher/ui/main_window.py`
- Modify: `launcher/app.py`
- Modify: `tests/test_launcher_bootstrap.py`
- Modify: `tests/test_launcher_app.py`

- [ ] **Step 1: Write the failing UI/API expectations**

Add test expectations that the window exposes:

```python
window.open_wechat_help_button
window.open_qq_help_button
```

and that `bind_social_channel_handlers(...)` accepts the two extra callbacks.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_bootstrap tests.test_launcher_app -v`
Expected: FAIL because the buttons and handlers do not exist yet.

- [ ] **Step 3: Implement the minimal UI/app wiring**

Update:

- `OpenClawLauncherWindow` to create two help buttons
- `bind_social_channel_handlers(...)` to accept and connect the callbacks
- `OpenClawLauncherApplication.show_main_window()` to pass the callbacks
- `OpenClawLauncherApplication` to add `_handle_open_wechat_help()` and `_handle_open_qq_help()`

Each handler should:

- open the packaged HTML page if present
- otherwise show a normal launcher error dialog

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_launcher_bootstrap tests.test_launcher_app -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add launcher/ui/main_window.py launcher/app.py tests/test_launcher_bootstrap.py tests/test_launcher_app.py
git commit -m "feat: wire wechat qq help actions"
```

### Task 4: Refine service-layer status text

**Files:**
- Modify: `launcher/services/social_channels.py`
- Modify: `tests/test_social_channel_service.py`

- [ ] **Step 1: Write the failing service tests**

Add assertions that:

- QQ `missing_runtime_plugin` maps to a launcher-facing label/detail
- WeChat `pending_enable` detail explicitly tells the user to click enable after QR success

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_social_channel_service -v`
Expected: FAIL because the refined label/detail mapping is not complete yet.

- [ ] **Step 3: Implement the minimal mapping changes**

Update `build_wechat_view_state()` and `build_qq_view_state()` so the details stay action-oriented and `missing_runtime_plugin` renders a direct launcher message.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_social_channel_service -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add launcher/services/social_channels.py tests/test_social_channel_service.py
git commit -m "feat: clarify wechat qq launcher statuses"
```

### Task 5: Full verification and context update

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
python -m unittest tests.test_social_channel_service tests.test_launcher_bootstrap tests.test_launcher_app tests.test_launcher_controller -v
```

Expected: PASS

- [ ] **Step 2: Run full verification**

Run:

```bash
python -m unittest discover -s tests
```

Expected: PASS

- [ ] **Step 3: Update project context**

Record:

- WeChat / QQ help entrypoints added
- refined launcher status wording
- verification evidence

- [ ] **Step 4: Validate context**

Run:

```bash
python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .
```

Expected: `context is valid`

- [ ] **Step 5: Commit**

```bash
git add .context/current-status.md .context/task-breakdown.md .context/work-log.md
git commit -m "docs: record wechat qq launcher help hardening"
```
