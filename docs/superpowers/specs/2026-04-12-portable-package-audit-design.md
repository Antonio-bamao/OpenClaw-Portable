# Portable Package Audit Design

## Goal

Add a read-only audit path for `dist/OpenClaw-Portable` so delivery work can be guided by measured package size, file count, dominant directories, required-file presence, and obvious U-disk write-risk paths.

## Scope

This pass does not prune files, rebuild packages, bump `version.json`, or publish a release. It only inspects a package directory and prints a JSON report.

## Behavior

- Audit a portable package root supplied by CLI, defaulting to `dist/OpenClaw-Portable`.
- Count total files and total bytes recursively.
- Produce largest directory summaries using stable POSIX-style relative paths.
- Check required runtime/package paths:
  - `OpenClawLauncher.exe`
  - `version.json`
  - `runtime/node/node.exe`
  - `runtime/openclaw/openclaw.mjs`
  - `runtime/openclaw/package.json`
  - `assets`
  - `tools`
  - `state/provider-templates`
- Flag write-risk directories inside the package when their path includes common cache/log/temp names: `logs`, `log`, `cache`, `.cache`, `tmp`, or `temp`.
- Warn when free space is supplied and is below the configured threshold, defaulting to 500MB.

## Architecture

- `launcher/services/portable_audit.py` owns the reusable scanner and dataclasses.
- `scripts/audit-portable-package.py` is a thin CLI wrapper that resolves the package path, calls the service, and prints JSON.
- Tests live in `tests/test_portable_audit.py` and cover service behavior plus the CLI path.

## Testing

Use `unittest`, following the repo’s existing temp-workspace helpers. Tests should create small fake package trees rather than relying on the real `dist/` directory.
