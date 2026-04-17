# WeChat / QQ Launcher Status Hardening Design

## Scope

This design improves the launcher-first WeChat and QQ channel experience without introducing new real-account dependencies, background daemons, or major UI layout changes.

Included:

- clearer WeChat stage mapping in the launcher
- clearer QQ status/error mapping in the launcher
- local help entry for WeChat and QQ setup
- launcher refresh after WeChat login so the user can see progress without guessing

Excluded:

- real WeChat / QQ E2E account validation
- new packaged runtime channels beyond the current WeChat / QQ slice
- broad UI redesign
- automated QQ platform registration or browser automation

## Goal

Make the existing launcher cards feel operational instead of half-configured by ensuring the user can always tell:

- what stage they are in
- what action is next
- whether the packaged runtime is missing required support

## Approach

Keep the existing card layout and button structure. Improve behavior through:

1. richer state mapping in the service layer
2. small controller/app refresh hooks
3. two local help pages opened from the launcher

This keeps the change low-risk and aligned with the current launcher architecture.

## Behavior

### WeChat

The launcher should present these states:

- `unconfigured`: plugin not installed
- `pending_login`: plugin installed, user should scan QR
- `pending_enable`: runtime status indicates login is complete, user should enable the channel
- `enabled`: launcher config has channel enabled
- `install_failed`
- `login_failed`

After the user clicks `扫码登录`, the launcher should continue to use the existing interactive terminal flow, then refresh the WeChat card state from likely runtime status files when the main view reloads.

The status detail should always tell the user the next action in plain Chinese.

### QQ

The launcher should present these states:

- `unconfigured`
- `invalid_config`
- `missing_runtime_plugin`
- `pending_enable`
- `enabled`

If the portable package contains a real OpenClaw runtime tree but the bundled `qqbot` extension is missing, QQ validation must fail with a direct message instead of allowing the user to proceed into a broken enable path.

QQ should continue to support the current credential-first launcher flow, and the runtime projection should include both config patch values and the documented env fallback values:

- `QQBOT_APP_ID`
- `QQBOT_CLIENT_SECRET`

## Help Entry

Add local help pages for:

- WeChat setup
- QQ setup

The launcher cards should expose one help button each that opens the packaged HTML help page in the system browser.

The help pages should contain only user-facing setup guidance:

- what the channel needs
- what each button does
- the usual failure modes
- the next step after success

## Architecture

### Service layer

`launcher/services/social_channels.py`

Responsibilities:

- map WeChat runtime status files into launcher state
- validate QQ packaged runtime support
- produce clearer status labels/details
- expose local help-relevant state cleanly

### Controller layer

`launcher/services/controller.py`

Responsibilities:

- reuse the richer service-layer state
- keep refresh behavior centralized
- avoid new cross-layer coupling

### App / UI layer

`launcher/app.py`
`launcher/ui/main_window.py`

Responsibilities:

- wire help buttons
- trigger card refresh after WeChat login actions
- display the richer state text without changing the overall layout structure

## Data Flow

### WeChat login flow

1. user clicks `安装微信插件`
2. launcher installs and records `pending_login`
3. user clicks `扫码登录`
4. launcher opens the existing interactive terminal flow
5. launcher reloads WeChat state from runtime status on refresh
6. once runtime indicates login success, state becomes `pending_enable`
7. user clicks `启用微信`

### QQ setup flow

1. user fills `AppID` and `AppSecret`
2. launcher saves credentials locally
3. user clicks `检查 QQ 配置`
4. launcher validates fields and bundled runtime support
5. if valid, state becomes `pending_enable`
6. user clicks `启用 QQ`

## Error Handling

- missing packaged QQ extension: show a direct packaged-runtime error
- missing WeChat runtime status file: keep current stage, do not invent success
- malformed WeChat runtime status file: ignore it and keep the last known launcher state
- help page missing from package: show a normal launcher error dialog

## Testing

Add or extend tests for:

- WeChat runtime status refresh into `pending_enable`
- QQ validation failure when packaged `qqbot` extension is missing
- QQ env projection
- help button wiring and packaged help-page existence
- launcher state application for the refined status labels

## Acceptance Criteria

- users can tell the next action for both WeChat and QQ from the card alone
- WeChat no longer stays ambiguously stuck after successful login state is written by runtime
- QQ no longer enables successfully against a packaged runtime missing its bundled extension
- packaged launcher exposes local help for both channels
- targeted tests and full test suite remain green
