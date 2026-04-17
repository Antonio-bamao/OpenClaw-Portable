# WeChat / QQ Real Onboarding Design

## Scope

This design extends the current launcher-assisted WeChat and QQ channel flow so the launcher can finish the critical onboarding step instead of stopping at local config projection.

Included:

- QQ real onboarding through the documented `openclaw channels add --channel qqbot --token "AppID:AppSecret"` command
- an explicit WeChat "confirm login completed" action so users do not rely only on passive refresh
- clearer launcher status messages for QQ onboarding success and failure

Excluded:

- real account E2E with live QQ / WeChat credentials
- browser automation for QQ Open Platform or WeChat QR login
- WeCom changes
- new background daemons or polling loops

## Goal

Make the launcher-owned setup flow feel complete:

- QQ enable should write the channel into the real OpenClaw runtime, not only into the launcher's local projection
- WeChat users should have a clear button to confirm QR login finished and immediately see the state advance

## Approaches Considered

### 1. Keep projection-only flow

Fastest, but QQ still stops short of the documented runtime onboarding step and users can end up with a launcher state that looks enabled before the runtime has actually accepted the channel.

### 2. Recommended: real QQ onboarding on first enable, explicit WeChat confirmation

Use the existing command runner to execute the documented QQ onboarding command during enable, then keep the current runtime projection as the launcher's stable config mirror. Add one small WeChat confirmation action that re-reads runtime status on demand.

This is the best fit for the current architecture: small surface area, real user value, and no new runtime daemon behavior.

### 3. Add background polling and richer diagnostics

More complete, but too large for this slice and it would add more moving parts than the launcher currently needs.

## Behavior

### WeChat

The WeChat card keeps the current install and QR-login flow, but adds a dedicated `确认已扫码` action.

Flow:

1. user installs the plugin
2. user clicks `扫码登录`
3. launcher opens the existing interactive login terminal
4. user finishes QR login outside the launcher
5. user clicks `确认已扫码`
6. launcher refreshes runtime status immediately
7. if runtime reports a logged-in state, the card moves to `待启用`

The button is a manual recovery/confirmation path. Passive refresh after login still stays in place.

### QQ

The QQ card keeps the current credential-first form, but `启用 QQ` now performs the documented onboarding command before marking the channel enabled.

Flow:

1. user saves `AppID` and `AppSecret`
2. launcher validates fields and bundled runtime support
3. on enable, launcher runs `channels add --channel qqbot --token "AppID:AppSecret"`
4. if the command succeeds, launcher saves QQ as enabled and reprojection continues as before
5. if the command fails, launcher keeps QQ disabled and shows a direct onboarding failure message

To avoid rerunning the add command on every enable, the launcher stores whether QQ has already been onboarded for the current credentials.

## Data Model

`QqChannelConfig` gains one persisted field:

- `last_onboarded_token_fingerprint: str | None`

The launcher stores a stable fingerprint derived from the trimmed `app_id` and `app_secret`. When the credentials change, the fingerprint changes too, so the next enable re-runs QQ onboarding.

No new WeChat config fields are required.

## Architecture

### Service layer

`launcher/services/social_channels.py`

Responsibilities:

- expose the QQ onboarding command arguments
- run the QQ onboarding command through the existing command runner
- track QQ onboarding state for the saved credentials
- expose an explicit WeChat runtime refresh action
- render launcher-facing status text for onboarding failure

### Controller layer

`launcher/services/controller.py`

Responsibilities:

- coordinate QQ validate -> onboard -> enable
- keep QQ disabled on onboarding failure
- expose a `confirm_wechat_channel_login()` action for the app layer

### App / UI layer

`launcher/ui/main_window.py`
`launcher/app.py`

Responsibilities:

- add the WeChat `确认已扫码` button
- wire the new confirmation action through the existing background action helper
- keep the current card layout intact

## Error Handling

- missing QQ credentials: stay in `invalid_config`
- missing bundled QQ runtime plugin: stay in `missing_runtime_plugin`
- QQ onboarding command failure: surface `enable_failed` with the command output
- WeChat runtime status still missing after confirmation: keep the prior stage, do not invent success
- malformed WeChat runtime status file: ignore it and keep the last known state

## Testing

Add or extend tests for:

- QQ onboarding command arguments
- QQ enable flow running real onboarding exactly once per credential set
- QQ enable flow staying disabled on command failure
- WeChat confirmation action refreshing state into `pending_enable`
- WeChat UI/app wiring for the new confirmation button

## Acceptance Criteria

- enabling QQ runs the documented `channels add --channel qqbot --token ...` command before the launcher marks QQ enabled
- re-enabling QQ with unchanged credentials does not rerun onboarding
- changing QQ credentials causes onboarding to run again on the next enable
- the WeChat card exposes a clear manual confirmation action after QR login
- targeted tests and the full suite remain green
