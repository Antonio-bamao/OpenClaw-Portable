from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher.services.runtime_pruning import DEFAULT_PRUNE_DIRECTORY_NAMES, DEFAULT_PRUNE_PATTERNS, prune_runtime_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prune safe-to-remove files from a portable runtime tree.")
    parser.add_argument("--runtime-path", required=True, help="Path to runtime/openclaw inside the portable dist.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed without deleting files.")
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Optional glob pattern to prune. Repeat to override the default patterns for experiments.",
    )
    parser.add_argument(
        "--directory-name",
        action="append",
        default=[],
        help="Optional directory name whose descendant files should be pruned during experiments.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    runtime_path = Path(args.runtime_path)
    has_explicit_overrides = bool(args.pattern or args.directory_name)
    patterns = tuple(args.pattern) if args.pattern else (() if has_explicit_overrides else DEFAULT_PRUNE_PATTERNS)
    directory_names = (
        tuple(args.directory_name)
        if args.directory_name
        else (() if has_explicit_overrides else DEFAULT_PRUNE_DIRECTORY_NAMES)
    )
    result = prune_runtime_tree(
        runtime_path,
        patterns=patterns,
        directory_names=directory_names,
        dry_run=args.dry_run,
    )
    print(
        json.dumps(
            {
                "runtime_path": str(runtime_path),
                "patterns": list(patterns),
                "directory_names": list(directory_names),
                "dry_run": args.dry_run,
                "files_removed": result.files_removed,
                "bytes_freed": result.bytes_freed,
                "freed_mb": round(result.bytes_freed / (1024 * 1024), 2),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
