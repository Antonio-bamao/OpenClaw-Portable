# Runtime Prune Candidate Audit Design

## Goal

Extend the read-only portable package audit so it can report runtime pruning candidates by risk level before we change default pruning rules.

## Scope

This pass does not delete files, change `DEFAULT_PRUNE_PATTERNS`, rebuild `dist`, bump versions, or publish a release. It only adds candidate groups to the audit JSON.

## Candidate Groups

- `source_maps`, low risk: `*.map`
- `markdown_docs`, low risk: `*.md`
- `type_declarations`, low risk: `*.d.ts`
- `typescript_sources`, medium risk: `*.ts`, `*.mts`, `*.cts`, excluding `*.d.ts`
- `test_artifacts`, medium risk: files whose name contains `.test.` or `.spec.`, and files under `__tests__` or `test` directories

Each group reports:

- `name`
- `risk`
- `description`
- `patterns`
- `total_files`
- `total_bytes`
- `total_mb`
- `sample_paths`

## Architecture

Keep the implementation inside `launcher/services/portable_audit.py` because it already owns package tree scanning and JSON reporting. Use the existing file-size map so the audit only walks the package once. `scripts/audit-portable-package.py` should emit the new field automatically through `to_dict()`.

## Acceptance Criteria

- `audit_portable_package()` includes `prune_candidates` in the result.
- Candidate grouping deduplicates files when multiple patterns match.
- `.d.ts` files are counted as `type_declarations`, not `typescript_sources`.
- The CLI JSON includes `prune_candidates`.
- The tool remains read-only.
