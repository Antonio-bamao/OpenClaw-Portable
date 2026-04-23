# OpenClaw Simple Startup Design

## Goal

Keep the current PySide launcher UI and channel/config surfaces, but replace the fragile startup path with a minimal OpenClaw boot flow modeled after a simpler reference desktop implementation: spawn bundled `node.exe` with `openclaw.mjs gateway run`, wait for the local gateway port to become reachable, then treat the runtime as started.

## Problem Summary

The current launcher has repeatedly hit startup regressions even when OpenClaw itself was able to boot successfully. Recent logs showed:

- `gateway ready`
- `browser control listening`
- `event-dispatch is ready`
- `ws client ready`

That means the OpenClaw runtime can start, but the launcher's extra orchestration is introducing failure modes:

- startup-time Feishu live probes can interfere with or delay the boot path
- the controller refresh path can misclassify runtime state after a successful boot
- Windows shows a blank console window because the GUI app launches `node.exe` without hiding the child console
- error copy currently implies "runtime exited early" in cases where the runtime actually booted and the launcher lost track of it

## Recommended Approach

Adopt the simpler reference boot model while keeping our existing UI shell:

1. Prepare config and environment before launch.
2. Spawn the bundled Node runtime with the OpenClaw entrypoint.
3. Poll only the gateway port/HTTP endpoint until it becomes reachable.
4. Do not run any startup-time channel probe or nonessential live verification.
5. After startup succeeds, keep status updates lightweight and avoid treating optional channel probes as startup-critical.

This keeps the launcher responsible for packaging, config projection, and UI, while moving startup success criteria back to the one thing that matters: "is the local gateway actually up?"

## Scope

### In Scope

- simplify `OpenClawRuntimeAdapter.start()` readiness checks
- align runtime process launch with the reference implementation's spawn pattern
- hide the Windows child console for the OpenClaw process
- remove startup-critical dependence on Feishu live probe results
- tighten controller/runtime error messaging so startup failure reflects actual process state
- add tests that lock in the simplified startup contract

### Out of Scope

- replacing the PySide UI with Electron
- copying the reference implementation's codebase wholesale
- redesigning channel onboarding UX
- changing the packaged OpenClaw version

## Architecture

### Runtime Launch

`launcher/runtime/openclaw_runtime.py` remains the single owner of process launch. It should:

- keep generating the runtime config and environment as it does now
- launch bundled `node.exe` + `openclaw.mjs gateway run --port ... --bind loopback --allow-unconfigured`
- hide the Windows console using `CREATE_NO_WINDOW`
- wait for readiness by checking actual gateway reachability rather than layered channel-specific probes

### Controller Behavior

`launcher/services/controller.py` should stop treating Feishu live probe output as a startup prerequisite or immediate post-start truth source. The controller may still support later channel health inspection, but startup and the main status badge should be derived from runtime reachability first.

### Error Reporting

`launcher/services/runtime_errors.py` should distinguish:

- process exited before the gateway was reachable
- gateway timed out but process is still alive
- runtime came up and later became unavailable

The user-facing error should match the observed state instead of defaulting to "提前退出".

## Data Flow

1. The launcher saves UI/provider/channel configuration.
2. The runtime adapter writes the merged runtime config to `state/runtime/openclaw.json`.
3. The runtime adapter launches the bundled Node process.
4. The runtime adapter polls the local gateway address until success or timeout.
5. The controller updates the UI from runtime state.
6. Optional channel inspection can happen later and must not retroactively invalidate startup success.

## Error Handling

- If the process exits before the gateway becomes reachable, report a true startup failure.
- If the process is alive but the gateway never becomes reachable before timeout, report a startup timeout.
- If the process successfully started and later dies, report that as a post-start runtime loss, not a boot failure.
- If channel probe data is unavailable, preserve runtime "running" unless the runtime itself is unreachable.

## Files Expected To Change

- `launcher/runtime/openclaw_runtime.py`
- `launcher/services/controller.py`
- `launcher/services/runtime_errors.py`
- `tests/test_openclaw_runtime_adapter.py`
- `tests/test_launcher_controller.py`
- `tests/test_launcher_app.py` or another launcher-facing test file if UI state transitions need new coverage

## Testing Strategy

- add/adjust runtime adapter tests for:
  - hidden Windows console launch
  - success when gateway reachability is observed
  - failure when the process exits before gateway readiness
- add/adjust controller tests for:
  - startup state no longer depending on Feishu probe
  - runtime status remaining "running" when optional probe data is absent
  - error state only when runtime reachability actually fails
- rerun the targeted launcher/runtime/channel test suite
- rebuild the packaged launcher and verify the new executable no longer opens the blank console window

## Why Not Replace Everything With The Reference App

The reference app is useful because its launch path is simple and robust, but it is not a drop-in replacement for this project:

- its portable mode is mostly script-driven and browser-driven
- its Electron app has a much smaller feature surface than this launcher
- replacing our UI shell would mean redoing updates, diagnostics, factory reset, and channel management instead of fixing the real issue

The right move is to borrow its startup model, not its whole app.
