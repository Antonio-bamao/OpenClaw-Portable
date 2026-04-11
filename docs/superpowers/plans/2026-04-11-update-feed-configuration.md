# Update Feed Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize the online update feed URL so production builds use a default feed address while developers can override it with `OPENCLAW_PORTABLE_UPDATE_FEED_URL`.

**Architecture:** Add a tiny resolver module that owns the default feed URL constant plus environment-variable precedence. Keep `OnlineUpdateService` focused on network/download behavior and have it consume the resolved URL instead of embedding env access or scattered literals.

**Tech Stack:** Python 3 standard library, `unittest`, existing launcher services.

---

### Task 1: Add failing tests for feed URL resolution

**Files:**
- Create: `tests/test_update_feed.py`
- Modify: `tests/test_online_update.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_resolve_update_feed_url_uses_default_when_no_override_exists(self) -> None:
    url = resolve_update_feed_url()
    self.assertEqual(url, DEFAULT_UPDATE_FEED_URL)

def test_resolve_update_feed_url_prefers_environment_override(self) -> None:
    os.environ["OPENCLAW_PORTABLE_UPDATE_FEED_URL"] = "https://staging.example.com/update.json"
    url = resolve_update_feed_url()
    self.assertEqual(url, "https://staging.example.com/update.json")

def test_online_update_service_uses_resolved_feed_url_when_no_explicit_url_is_passed(self) -> None:
    service = OnlineUpdateService(paths)
    self.assertEqual(service.update_feed_url, expected)
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m unittest tests.test_update_feed tests.test_online_update -v`
Expected: FAIL because the resolver module and integration do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
DEFAULT_UPDATE_FEED_URL = "https://example.com/openclaw-portable/update.json"

def resolve_update_feed_url(requested_url: str | None = None) -> str:
    ...
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m unittest tests.test_update_feed tests.test_online_update -v`
Expected: PASS

### Task 2: Wire the resolver into the online update service and verify regressions

**Files:**
- Create: `launcher/services/update_feed.py`
- Modify: `launcher/services/online_update.py`

- [ ] **Step 1: Run the scoped regression suite**

Run: `python -m unittest tests.test_update_feed tests.test_online_update tests.test_launcher_controller -v`
Expected: PASS

- [ ] **Step 2: Run the broader suite available in this environment**

Run: `python -m unittest discover -s tests`
Expected: PASS except for the pre-existing `PySide6` import failures in UI-oriented modules.

### Task 3: Update project context and validate it

**Files:**
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`
- Modify: `.context/work-log.md`
- Modify: `.context/decisions.md`

- [ ] **Step 1: Record the feed configuration rule**

```text
Document that online update now resolves its feed URL from an explicit override, then `OPENCLAW_PORTABLE_UPDATE_FEED_URL`, then a centralized production default.
```

- [ ] **Step 2: Validate project context**

Run: `python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .`
Expected: `context is valid`
