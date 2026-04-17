# WeChat / QQ Real Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make QQ enable perform real runtime onboarding and add an explicit WeChat login confirmation action in the launcher.

**Architecture:** Extend the social channel service with a QQ onboarding command plus credential fingerprint tracking, then wire controller and app/UI flows so QQ enable runs the real command and WeChat exposes a manual confirmation refresh action.

**Tech Stack:** Python 3.12, PySide6, unittest, OpenClaw packaged runtime command runner

---

### Task 1: Add failing service tests for QQ onboarding and WeChat confirmation

**Files:**
- Modify: `tests/test_social_channel_service.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:

```python
self.assertEqual(
    service.qq_onboarding_command(QqChannelConfig(app_id="123456", app_secret="secret")),
    ["channels", "add", "--channel", "qqbot", "--token", "123456:secret"],
)
```

and:

```python
service.confirm_wechat_runtime_login()
state = service.build_wechat_view_state()
self.assertEqual(state.status_label, "待启用")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_social_channel_service -v`
Expected: FAIL because the new service methods do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add:

- QQ onboarding command builder
- QQ onboarding runner
- WeChat explicit runtime refresh helper

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_social_channel_service -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_social_channel_service.py launcher/services/social_channels.py
git commit -m "test: cover qq onboarding and wechat confirmation"
```

### Task 2: Add failing controller tests for real QQ enable flow

**Files:**
- Modify: `tests/test_launcher_controller.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:

```python
enabled_qq = controller.enable_qq_channel()
self.assertEqual(fake_runner.calls[-1], ["channels", "add", "--channel", "qqbot", "--token", "123456:secret"])
self.assertTrue(enabled_qq.enabled)
```

and:

```python
state = controller.enable_qq_channel()
self.assertFalse(state.enabled)
self.assertIn("channels add", state.status_detail)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_controller -v`
Expected: FAIL because enable still only validates and reprojections.

- [ ] **Step 3: Write minimal implementation**

Update controller enable logic to:

1. validate config
2. run QQ onboarding when credentials are not yet onboarded
3. save `enabled=True` only on success
4. keep disabled and save an error status on failure

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_launcher_controller.py launcher/services/controller.py launcher/services/social_channels.py
git commit -m "feat: onboard qq channel on enable"
```

### Task 3: Add failing app/UI tests for WeChat confirmation action

**Files:**
- Modify: `tests/test_launcher_app.py`
- Modify: `tests/test_launcher_bootstrap.py`
- Modify: `launcher/app.py`
- Modify: `launcher/ui/main_window.py`

- [ ] **Step 1: Write the failing tests**

Add assertions for:

```python
self.assertEqual(window.confirm_wechat_button.text(), "确认已扫码")
```

and:

```python
application._handle_confirm_wechat_channel()
self.assertIn("confirm_wechat_channel_login", calls)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_bootstrap -v`
Expected: FAIL because the button and handler do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add the new WeChat button, bind it through `bind_social_channel_handlers(...)`, and wire a background handler that refreshes the card and main view.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_launcher_app tests.test_launcher_bootstrap -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_launcher_app.py tests/test_launcher_bootstrap.py launcher/app.py launcher/ui/main_window.py
git commit -m "feat: add wechat login confirmation action"
```

### Task 4: Full verification and context update

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
python -m unittest tests.test_social_channel_service tests.test_launcher_controller tests.test_launcher_app tests.test_launcher_bootstrap -v
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

- QQ now performs real onboarding on enable
- WeChat now exposes explicit login confirmation
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
git commit -m "docs: record qq onboarding and wechat confirmation"
```
