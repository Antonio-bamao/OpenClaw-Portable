from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_PRUNE_PATTERNS = ("*.map", "*.md", "*.d.ts")


@dataclass(frozen=True)
class RuntimePruneResult:
    files_removed: int
    bytes_freed: int


def prune_runtime_tree(
    runtime_root: Path,
    *,
    patterns: tuple[str, ...] = DEFAULT_PRUNE_PATTERNS,
    dry_run: bool = False,
) -> RuntimePruneResult:
    candidates = _collect_prunable_files(runtime_root, patterns)
    bytes_freed = sum(candidate.stat().st_size for candidate in candidates)
    if not dry_run:
        for candidate in candidates:
            candidate.unlink(missing_ok=True)
    return RuntimePruneResult(files_removed=len(candidates), bytes_freed=bytes_freed)


def _collect_prunable_files(runtime_root: Path, patterns: tuple[str, ...]) -> list[Path]:
    candidates: dict[Path, None] = {}
    for pattern in patterns:
        for candidate in runtime_root.rglob(pattern):
            if candidate.is_file():
                candidates[candidate] = None
    return sorted(candidates.keys())
