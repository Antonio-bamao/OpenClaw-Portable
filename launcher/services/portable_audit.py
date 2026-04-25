from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from launcher.services.runtime_pruning import DEFAULT_PRESERVE_PATTERNS

DEFAULT_RUNTIME_PRESERVE_PATHS = tuple(f"runtime/openclaw/{pattern}" for pattern in DEFAULT_PRESERVE_PATTERNS)


DEFAULT_REQUIRED_PATHS = (
    "OpenClawLauncher.exe",
    "version.json",
    "runtime/node/node.exe",
    "runtime/openclaw/openclaw.mjs",
    "runtime/openclaw/package.json",
    "assets",
    "tools",
    "state/provider-templates",
)
DEFAULT_MIN_FREE_SPACE_BYTES = 500 * 1024 * 1024
WRITE_RISK_DIR_NAMES = {"logs", "log", "cache", ".cache", "tmp", "temp"}
ALLOWED_RELEASE_STATE_ENTRIES = {"provider-templates"}
DEFAULT_PRUNE_CANDIDATE_RULES = (
    {
        "name": "source_maps",
        "risk": "low",
        "description": "Source map files already removed by the default release pruning step.",
        "patterns": ("*.map",),
    },
    {
        "name": "markdown_docs",
        "risk": "low",
        "description": "Markdown documentation files already removed by the default release pruning step.",
        "patterns": ("*.md",),
        "exclude_patterns": DEFAULT_RUNTIME_PRESERVE_PATHS,
    },
    {
        "name": "type_declarations",
        "risk": "low",
        "description": "TypeScript declaration files already removed by the default release pruning step.",
        "patterns": ("*.d.ts",),
    },
    {
        "name": "typescript_sources",
        "risk": "medium",
        "description": "TypeScript source files that need real runtime smoke validation before becoming default pruning rules.",
        "patterns": ("*.ts", "*.mts", "*.cts"),
        "exclude_patterns": ("*.d.ts",),
    },
    {
        "name": "test_artifacts",
        "risk": "medium",
        "description": "Test-like files that need validation before pruning from the packaged runtime.",
        "patterns": ("*.test.*", "*.spec.*"),
        "directory_names": ("__tests__", "test"),
    },
)


@dataclass(frozen=True)
class PortablePruneCandidateGroup:
    name: str
    risk: str
    description: str
    patterns: tuple[str, ...]
    total_bytes: int
    total_files: int
    sample_paths: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "risk": self.risk,
            "description": self.description,
            "patterns": list(self.patterns),
            "total_bytes": self.total_bytes,
            "total_mb": round(self.total_bytes / (1024 * 1024), 2),
            "total_files": self.total_files,
            "sample_paths": self.sample_paths,
        }


@dataclass(frozen=True)
class PortableDirectorySummary:
    relative_path: str
    total_bytes: int
    file_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "total_bytes": self.total_bytes,
            "total_mb": round(self.total_bytes / (1024 * 1024), 2),
            "file_count": self.file_count,
        }


@dataclass(frozen=True)
class PortablePackageAuditResult:
    package_root: Path
    total_bytes: int
    total_files: int
    top_directories: list[PortableDirectorySummary]
    required_paths_missing: list[str]
    unexpected_state_paths: list[str]
    write_risk_directories: list[str]
    prune_candidates: list[PortablePruneCandidateGroup]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "package_root": str(self.package_root),
            "total_bytes": self.total_bytes,
            "total_mb": round(self.total_bytes / (1024 * 1024), 2),
            "total_files": self.total_files,
            "top_directories": [summary.to_dict() for summary in self.top_directories],
            "required_paths_missing": self.required_paths_missing,
            "unexpected_state_paths": self.unexpected_state_paths,
            "write_risk_directories": self.write_risk_directories,
            "prune_candidates": [candidate.to_dict() for candidate in self.prune_candidates],
            "warnings": self.warnings,
        }


def audit_portable_package(
    package_root: Path,
    *,
    top_limit: int = 10,
    free_space_bytes: int | None = None,
    min_free_space_bytes: int = DEFAULT_MIN_FREE_SPACE_BYTES,
    required_paths: tuple[str, ...] = DEFAULT_REQUIRED_PATHS,
) -> PortablePackageAuditResult:
    if not package_root.exists():
        raise FileNotFoundError(f"Portable package root does not exist: {package_root}")
    if not package_root.is_dir():
        raise NotADirectoryError(f"Portable package root is not a directory: {package_root}")

    file_sizes = _collect_file_sizes(package_root)
    directory_summaries = _summarize_directories(package_root, file_sizes)
    unexpected_state_paths = find_unexpected_release_state_paths(package_root)
    write_risk_directories = _find_write_risk_directories(package_root)
    prune_candidates = _collect_prune_candidates(package_root, file_sizes)
    warnings = _build_warnings(
        free_space_bytes=free_space_bytes,
        min_free_space_bytes=min_free_space_bytes,
        unexpected_state_paths=unexpected_state_paths,
        write_risk_directories=write_risk_directories,
    )

    return PortablePackageAuditResult(
        package_root=package_root,
        total_bytes=sum(file_sizes.values()),
        total_files=len(file_sizes),
        top_directories=directory_summaries[: max(top_limit, 0)],
        required_paths_missing=[relative_path for relative_path in required_paths if not (package_root / relative_path).exists()],
        unexpected_state_paths=unexpected_state_paths,
        write_risk_directories=write_risk_directories,
        prune_candidates=prune_candidates,
        warnings=warnings,
    )


def find_unexpected_release_state_paths(package_root: Path) -> list[str]:
    state_root = package_root / "state"
    if not state_root.exists():
        return []
    return [
        _relative_posix(package_root, child)
        for child in sorted(state_root.iterdir(), key=lambda item: item.name.lower())
        if child.name not in ALLOWED_RELEASE_STATE_ENTRIES
    ]


def assert_release_state_clean(package_root: Path) -> None:
    unexpected_paths = find_unexpected_release_state_paths(package_root)
    if unexpected_paths:
        paths_text = ", ".join(unexpected_paths)
        raise ValueError(f"Portable package contains mutable state entries that should not be released: {paths_text}")


def _collect_file_sizes(package_root: Path) -> dict[Path, int]:
    file_sizes: dict[Path, int] = {}
    for path in package_root.rglob("*"):
        if path.is_file():
            file_sizes[path] = path.stat().st_size
    return file_sizes


def _summarize_directories(package_root: Path, file_sizes: dict[Path, int]) -> list[PortableDirectorySummary]:
    totals: dict[Path, list[int]] = {}
    for file_path, size in file_sizes.items():
        current = file_path.parent
        while current != package_root.parent:
            if current != package_root:
                directory_total = totals.setdefault(current, [0, 0])
                directory_total[0] += size
                directory_total[1] += 1
            if current == package_root:
                break
            current = current.parent
    summaries = [
        PortableDirectorySummary(_relative_posix(package_root, directory), total[0], total[1])
        for directory, total in totals.items()
    ]
    return sorted(summaries, key=lambda summary: (-summary.total_bytes, -summary.file_count, summary.relative_path))


def _find_write_risk_directories(package_root: Path) -> list[str]:
    risky: list[str] = []
    for path in package_root.rglob("*"):
        relative_parts = path.relative_to(package_root).parts
        if path.is_dir() and _is_write_risk_directory(relative_parts):
            risky.append(_relative_posix(package_root, path))
    return sorted(risky)


def _collect_prune_candidates(package_root: Path, file_sizes: dict[Path, int]) -> list[PortablePruneCandidateGroup]:
    groups: list[PortablePruneCandidateGroup] = []
    for rule in DEFAULT_PRUNE_CANDIDATE_RULES:
        matches = [
            path
            for path in sorted(file_sizes.keys())
            if _matches_prune_candidate_rule(path.relative_to(package_root), rule)
        ]
        groups.append(
            PortablePruneCandidateGroup(
                name=str(rule["name"]),
                risk=str(rule["risk"]),
                description=str(rule["description"]),
                patterns=tuple(str(pattern) for pattern in rule.get("patterns", ())),
                total_bytes=sum(file_sizes[path] for path in matches),
                total_files=len(matches),
                sample_paths=[path.relative_to(package_root).as_posix() for path in matches[:5]],
            )
        )
    return groups


def _matches_prune_candidate_rule(relative_path: Path, rule: dict[str, object]) -> bool:
    relative_posix = relative_path.as_posix()
    name = relative_path.name
    exclude_patterns = tuple(str(pattern) for pattern in rule.get("exclude_patterns", ()))
    if any(fnmatch(name, pattern) or fnmatch(relative_posix, pattern) for pattern in exclude_patterns):
        return False
    patterns = tuple(str(pattern) for pattern in rule.get("patterns", ()))
    if any(fnmatch(name, pattern) or fnmatch(relative_posix, pattern) for pattern in patterns):
        return True
    directory_names = set(str(part) for part in rule.get("directory_names", ()))
    return any(part in directory_names for part in relative_path.parts[:-1])


def _is_write_risk_directory(relative_parts: tuple[str, ...]) -> bool:
    lowered_parts = tuple(part.lower() for part in relative_parts)
    if not lowered_parts or lowered_parts[-1] not in WRITE_RISK_DIR_NAMES:
        return False
    if "node_modules" in lowered_parts:
        return False
    return len(lowered_parts) == 1 or lowered_parts[0] in {"state", "runtime"}


def _build_warnings(
    *,
    free_space_bytes: int | None,
    min_free_space_bytes: int,
    unexpected_state_paths: list[str],
    write_risk_directories: list[str],
) -> list[str]:
    warnings: list[str] = []
    if free_space_bytes is not None and free_space_bytes < min_free_space_bytes:
        warnings.append(f"Free space is below {_format_mb(min_free_space_bytes)}.")
    if unexpected_state_paths:
        warnings.append("Package contains mutable state entries that should not be released.")
    if write_risk_directories:
        warnings.append("Package contains cache/log/temp directories that may increase U disk writes.")
    return warnings


def _format_mb(bytes_count: int) -> str:
    return f"{bytes_count / (1024 * 1024):.2f} MB"


def _relative_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
