from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


DEFAULT_PRUNE_PATTERNS = (
    "*.map",
    "*.md",
    "*.d.ts",
    "*.ts",
    "*.mts",
    "*.cts",
    "*.test.*",
    "*.spec.*",
)
DEFAULT_PRUNE_DIRECTORY_NAMES = ("__tests__", "test")
DEFAULT_PRESERVE_PATTERNS = ("docs/reference/templates/*.md",)


@dataclass(frozen=True)
class RuntimePruneResult:
    files_removed: int
    bytes_freed: int


def prune_runtime_tree(
    runtime_root: Path,
    *,
    patterns: tuple[str, ...] = DEFAULT_PRUNE_PATTERNS,
    directory_names: tuple[str, ...] = DEFAULT_PRUNE_DIRECTORY_NAMES,
    preserve_patterns: tuple[str, ...] = DEFAULT_PRESERVE_PATTERNS,
    dry_run: bool = False,
) -> RuntimePruneResult:
    candidates = _collect_prunable_files(runtime_root, patterns, directory_names, preserve_patterns)
    bytes_freed = sum(candidate.stat().st_size for candidate in candidates)
    if not dry_run:
        for candidate in candidates:
            candidate.unlink(missing_ok=True)
    return RuntimePruneResult(files_removed=len(candidates), bytes_freed=bytes_freed)


def _collect_prunable_files(
    runtime_root: Path,
    patterns: tuple[str, ...],
    directory_names: tuple[str, ...],
    preserve_patterns: tuple[str, ...],
) -> list[Path]:
    candidates: dict[Path, None] = {}
    directory_name_set = {name for name in directory_names if name}
    for candidate in runtime_root.rglob("*"):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(runtime_root)
        relative_posix = relative_path.as_posix()
        if any(fnmatch(candidate.name, pattern) or fnmatch(relative_posix, pattern) for pattern in preserve_patterns):
            continue
        if any(fnmatch(candidate.name, pattern) or fnmatch(relative_posix, pattern) for pattern in patterns):
            candidates[candidate] = None
            continue
        if directory_name_set and any(part in directory_name_set for part in relative_path.parts[:-1]):
            candidates[candidate] = None
    return sorted(candidates.keys())
