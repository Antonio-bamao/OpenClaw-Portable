# 2026-04-25 Provider Bridge Runtime Auth Design

## Background

The portable launcher currently stores provider selection in its own state:

- `state/openclaw.json`
- `state/.env`

That is enough for launcher UI copy and basic runtime startup, but it does not fully configure the embedded OpenClaw runtime's native model/auth system.

The result is a split-brain experience:

- the launcher can show `dashscope / qwen-max`
- the embedded web chat can still run with OpenClaw's default chat model such as `openai/gpt-5.4`
- the runtime then looks for `state/agents/main/agent/auth-profiles.json`
- that file is currently missing, so chat fails with `No API key found for provider "openai"`

This is not a DashScope/Qwen-only bug. It is an integration gap between launcher-managed provider settings and OpenClaw-native runtime configuration.

## Goal

Introduce a provider bridge so launcher configuration becomes the source of truth for the embedded OpenClaw runtime's default chat model and main-agent auth store.

After this work:

- a launcher-configured provider is reflected in the embedded OpenClaw runtime
- the main chat agent uses the selected provider/model instead of falling back to unrelated defaults
- the main agent gets a valid `auth-profiles.json` for API-key-based providers
- DashScope/Qwen, OpenAI, Anthropic, DeepSeek, OpenRouter, and OpenAI-compatible custom providers all follow the same bridge path

## Non-Goals

- Rebuilding the launcher wizard into a full clone of OpenClaw's native onboarding
- Solving every provider-specific feature in one pass
- Configuring image/audio/video generation provider trees in this round
- Reworking session-level `/model` switching UI
- Replacing OpenClaw's native auth/profile architecture

## User Problem

The user expectation is straightforward:

- If they select a provider in the launcher and enter a valid API key, the embedded chat should use that provider.
- If they enter a DashScope/Qwen API key, the runtime should not ask for an OpenAI key.
- OpenAI credentials and Anthropic credentials must also be handled as first-class types rather than forcing everything through one generic key slot.
- The architecture should be extensible enough to support mainstream model vendors that OpenClaw already supports.

## Proposed Approach

Add a dedicated provider bridge layer between launcher config storage and OpenClaw runtime preparation.

The bridge will:

1. Read launcher-managed provider config from `LauncherConfig` and `SensitiveConfig`
2. Resolve that config into a normalized runtime provider target
3. Generate OpenClaw-native runtime config for the default chat model
4. Generate OpenClaw-native main-agent auth store content
5. Write both artifacts before runtime startup and before any runtime re-projection path completes

This keeps the launcher UI simple while aligning the embedded runtime with OpenClaw's real model/auth system.

## Architecture

### 1. New Provider Bridge Service

Introduce a new launcher service, conceptually:

- `launcher/services/provider_bridge.py`

Responsibilities:

- detect the effective runtime provider type
- normalize launcher provider settings into OpenClaw model/provider identifiers
- build runtime config patch for OpenClaw-native model selection
- build main-agent auth profile document for API-key auth
- apply only the fields owned by the launcher bridge

This service should be small and deterministic. It should not start processes or make network calls.

### 2. Two Output Targets

The bridge writes into two OpenClaw-native locations.

#### A. Runtime config

Target:

- `state/runtime/openclaw.json`

Purpose:

- set the default chat model used by the embedded runtime
- add provider configuration required by OpenClaw for custom-compatible endpoints
- keep provider/model routing aligned with launcher selection

At minimum, the bridge must write launcher-owned fields under the OpenClaw runtime config for:

- `agents.defaults.model.primary`
- optional allowlist/catalog entries when needed
- provider-specific config under `models.providers.*` when the selected provider requires explicit config instead of simple env-only auth

#### B. Main-agent auth store

Target:

- `state/agents/main/agent/auth-profiles.json`

Purpose:

- provide the main agent with the API-key auth profile required by the selected provider
- ensure web chat, direct agent runs, and agent-spawned work all read compatible auth data

The bridge owns only provider-auth content needed for launcher-managed primary chat usage.

## Provider Detection Rules

Detection should prefer explicit launcher metadata first, then fall back to URL/model heuristics.

### Priority Order

1. `provider_id`
2. `base_url`
3. `model`

### Supported Types In Scope

#### `openai`

Match when:

- `provider_id == "openai"`
- or base URL points to `api.openai.com`
- or model is explicitly prefixed with `openai/`

Result:

- primary model becomes `openai/<model>`
- auth profile is created for OpenAI API-key auth

#### `anthropic`

Match when:

- `provider_id == "anthropic"`
- or base URL points to `api.anthropic.com`
- or model is explicitly prefixed with `anthropic/`

Result:

- primary model becomes `anthropic/<model>`
- auth profile is created for Anthropic API-key auth

#### `qwen`

Match when:

- `provider_id` is `dashscope` or `qwen`
- or base URL matches DashScope/Coding DashScope domains
- or model name looks like a Qwen text model such as `qwen-max`, `qwen-plus`, `qwen-turbo`

Result:

- primary model becomes `qwen/<model>` when model does not already contain a provider prefix
- auth profile is created for Qwen API-key auth

#### `deepseek`

Match when:

- `provider_id == "deepseek"`
- or base URL points to `api.deepseek.com`
- or model looks like `deepseek-chat` or `deepseek-reasoner`

Result:

- primary model becomes `deepseek/<model>`
- auth profile is created for DeepSeek API-key auth

#### `openrouter`

Match when:

- `provider_id == "openrouter"`
- or base URL points to `openrouter.ai`

Result:

- primary model becomes `openrouter/<model>` unless already provider-qualified
- auth profile is created for OpenRouter API-key auth

#### `custom-compatible`

Match when:

- no known provider type matched
- but launcher config still has non-empty `base_url`, `model`, and API key

Result:

- do not coerce to `openai`
- create a custom provider entry under OpenClaw runtime config
- set primary model to a launcher-owned custom provider/model identifier
- create auth profile for that custom provider

This preserves compatibility with OpenAI-style gateways and third-party hosted model platforms.

## Model Mapping Rules

### Canonicalization

If the selected model already includes a provider prefix, preserve it when it matches the resolved provider.

Examples:

- `openai/gpt-5.4` stays `openai/gpt-5.4`
- `anthropic/claude-sonnet-4-6` stays as-is
- `openrouter/openai/gpt-4.1-mini` stays as-is

If the selected model is not provider-qualified:

- Qwen: `qwen-max` -> `qwen/qwen-max`
- DeepSeek: `deepseek-chat` -> `deepseek/deepseek-chat`
- OpenAI: `gpt-5.4` -> `openai/gpt-5.4`
- Anthropic: `claude-sonnet-4-6` -> `anthropic/claude-sonnet-4-6`

### Default Chat Model

The bridge controls only the launcher-managed primary chat model:

- `agents.defaults.model.primary`

Fallback chains are out of scope for this round unless a provider requires a minimal compatibility fallback to stay valid. The default implementation should keep fallbacks untouched unless the launcher explicitly owns them later.

## Auth Profile Rules

### Main-Agent Scope

The bridge must generate:

- `state/agents/main/agent/auth-profiles.json`

This file should exist whenever launcher-managed API-key auth is complete.

### Managed Profile Shape

The bridge should write a launcher-owned default profile per provider, rather than inventing ad hoc storage outside OpenClaw's auth system.

Minimum requirements:

- provider identity is explicit
- API key is stored in the auth-profile store format expected by the runtime
- repeated launcher reconfiguration updates the same launcher-owned profile rather than creating duplicates

The bridge should use stable launcher-owned profile IDs, for example:

- `openai:launcher`
- `anthropic:launcher`
- `qwen:launcher`
- `deepseek:launcher`
- `openrouter:launcher`
- `custom-compatible:launcher`

Exact JSON shape should follow the runtime's expected `auth-profiles.json` schema rather than inventing a launcher-only variation.

## Ownership and Overwrite Policy

This bridge must be safe in a dirty runtime state.

### Launcher-Owned Fields

The launcher may overwrite:

- launcher-owned model primary config
- launcher-owned custom provider entries
- launcher-owned auth profiles in `main` agent auth store

### Launcher Must Not Overwrite

The launcher must not destroy or rewrite:

- sessions
- channel runtime state
- workspace content
- unrelated agent config
- unrelated auth profiles not owned by the launcher bridge

### Conflict Policy

For the main agent's primary chat provider, launcher config wins.

Reason:

- the launcher is the explicit UI users are using to choose provider/model/key
- the current bug exists because runtime defaults are diverging from launcher config

However, the overwrite scope must remain narrow:

- update only bridge-owned profile IDs
- preserve unknown auth profiles
- patch runtime config instead of replacing the whole document

## Runtime Integration Points

The bridge must run anywhere launcher config is projected into runtime state.

Minimum integration points:

- `LauncherController.configure()`
- `_prepare_if_needed()`
- `_reproject_channels_if_configured()`

This ensures:

- first save is enough
- restart/reconfigure paths stay consistent
- channel projection and provider projection can coexist

## Error Handling

### Missing API Key

If provider/model are configured but API key is empty:

- runtime config may still set the selected default model
- auth profile must not claim valid credentials
- launcher UI should continue surfacing "API Key not configured" style messaging

This preserves current offline-ish behavior without generating false-valid auth state.

### Unknown Provider

If the provider cannot be matched but `base_url + model + api_key` exist:

- route to `custom-compatible`
- do not silently fall back to `openai`

### Incomplete Custom Provider

If `custom` is selected but `base_url` or `model` is missing:

- do not generate invalid runtime provider config
- keep existing launcher validation behavior

### Auth Store Read/Write Corruption

If `auth-profiles.json` exists but is unreadable:

- fail safe by rebuilding only launcher-owned profile content if possible
- preserve a narrow recovery path instead of crashing with a generic runtime auth failure

## Testing Strategy

### Unit Tests

Add focused tests for:

- provider detection:
  - OpenAI
  - Anthropic
  - Qwen/DashScope
  - DeepSeek
  - OpenRouter
  - custom-compatible
- model canonicalization
- runtime config patch generation
- auth profile document generation
- merge behavior preserving unrelated auth profiles

### Controller Integration Tests

Add tests proving that:

- launcher config produces provider bridge output during `configure()`
- runtime `prepare()` receives provider/runtime patches together with existing channel patches
- a DashScope config no longer results in an OpenAI auth lookup path
- OpenAI and Anthropic selections generate their own provider-specific auth types

### Regression Tests

Must explicitly cover:

1. DashScope + `qwen-max` + valid key
   - no `openai` auth lookup failure
   - primary chat model resolves to Qwen

2. OpenAI + `gpt-5.4`
   - main agent auth store exists
   - runtime primary model resolves to OpenAI

3. Anthropic + `claude-sonnet-4-6`
   - main agent auth store exists
   - runtime primary model resolves to Anthropic

## Rollout Plan

### Phase 1

Bridge support for:

- OpenAI
- Anthropic
- Qwen
- DeepSeek
- OpenRouter
- custom-compatible

### Phase 2

If needed later:

- broaden built-in launcher provider templates
- support richer fallback/default catalogs
- support multimodal provider trees and non-text defaults

## Risks

### Risk: wrong provider inference

Mitigation:

- explicit `provider_id` always wins
- URL/model heuristics are fallback only
- tests cover ambiguous cases

### Risk: corrupting user-managed auth profiles

Mitigation:

- stable launcher-owned profile IDs
- merge instead of replace
- preserve unrelated profiles

### Risk: runtime config divergence remains hidden

Mitigation:

- all runtime prepare paths use the bridge
- tests assert runtime patch presence, not just launcher config persistence

## Success Criteria

This design is successful when all of the following are true:

- A launcher-selected provider becomes the embedded OpenClaw chat provider
- DashScope/Qwen API keys do not trigger OpenAI credential errors
- OpenAI credentials work as OpenAI credentials
- Anthropic credentials work as Anthropic credentials
- The bridge architecture is extendable to additional mainstream providers already supported by OpenClaw
- The launcher no longer behaves like a Qwen-only special case
