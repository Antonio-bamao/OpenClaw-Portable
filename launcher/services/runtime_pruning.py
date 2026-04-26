from __future__ import annotations

import os
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
    bytes_freed = sum(_file_size(candidate) for candidate in candidates)
    if not dry_run:
        for candidate in candidates:
            _unlink_file(candidate)
    return RuntimePruneResult(files_removed=len(candidates), bytes_freed=bytes_freed)


def _collect_prunable_files(
    runtime_root: Path,
    patterns: tuple[str, ...],
    directory_names: tuple[str, ...],
    preserve_patterns: tuple[str, ...],
) -> list[Path]:
    candidates: dict[Path, None] = {}
    directory_name_set = {name for name in directory_names if name}
    for candidate in _iter_files(runtime_root):
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


def _iter_files(root: Path) -> list[Path]:
    if os.name != "nt":
        return [item for item in root.rglob("*") if item.is_file()]

    root = root.resolve()
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(_long_path(root)):
        for filename in filenames:
            files.append(Path(_strip_long_path(os.path.join(dirpath, filename))))
    return files


def _file_size(path: Path) -> int:
    return os.path.getsize(_long_path(path))


def _unlink_file(path: Path) -> None:
    try:
        os.remove(_long_path(path))
    except FileNotFoundError:
        return


def _long_path(path: Path) -> str:
    text = str(path)
    if os.name != "nt" or text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def _strip_long_path(path: str) -> str:
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path.removeprefix("\\\\?\\UNC\\")
    if path.startswith("\\\\?\\"):
        return path.removeprefix("\\\\?\\")
    return path
