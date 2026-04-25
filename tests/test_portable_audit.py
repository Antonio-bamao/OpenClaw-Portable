import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from launcher.services.portable_audit import audit_portable_package


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"portable-audit-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PortableAuditTests(unittest.TestCase):
    def test_audit_counts_files_bytes_and_largest_directories(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_file(package_root / "OpenClawLauncher.exe", "exe")
            write_file(package_root / "version.json", "{}")
            write_file(package_root / "runtime" / "node" / "node.exe", "node")
            write_file(package_root / "runtime" / "openclaw" / "openclaw.mjs", "mjs")
            write_file(package_root / "runtime" / "openclaw" / "package.json", "{}")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "entry.js", "1234567890")
            write_file(package_root / "assets" / "logo.png", "png")
            write_file(package_root / "tools" / "export-diag.bat", "bat")
            write_file(package_root / "state" / "provider-templates" / "qwen.json", "{}")

            result = audit_portable_package(package_root, top_limit=3)

            self.assertEqual(result.total_files, 9)
            self.assertEqual(result.total_bytes, 32)
            self.assertEqual(result.required_paths_missing, [])
            self.assertEqual(result.top_directories[0].relative_path, "runtime")
            self.assertEqual(result.top_directories[1].relative_path, "runtime/openclaw")
            self.assertEqual(result.top_directories[0].file_count, 4)
            self.assertEqual(result.top_directories[1].total_bytes, 15)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audit_flags_missing_required_paths_write_risk_and_low_space(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_file(package_root / "version.json", "{}")
            write_file(package_root / "runtime" / "openclaw" / "cache" / "warm.bin", "cache")
            write_file(package_root / "runtime" / "openclaw" / "node_modules" / "undici" / "lib" / "cache" / "index.js", "code")
            write_file(package_root / "logs" / "launcher.log", "log")
            write_file(package_root / "state" / "logs" / "openclaw.log", "state log")

            result = audit_portable_package(
                package_root,
                free_space_bytes=200 * 1024 * 1024,
                min_free_space_bytes=500 * 1024 * 1024,
            )

            self.assertIn("OpenClawLauncher.exe", result.required_paths_missing)
            self.assertIn("runtime/node/node.exe", result.required_paths_missing)
            self.assertIn("runtime/openclaw/openclaw.mjs", result.required_paths_missing)
            self.assertEqual(result.unexpected_state_paths, ["state/logs"])
            self.assertEqual(result.write_risk_directories, ["logs", "runtime/openclaw/cache", "state/logs"])
            self.assertIn("Free space is below 500.00 MB.", result.warnings)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audit_reports_mutable_state_entries_but_allows_provider_templates(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_file(package_root / "state" / "provider-templates" / "qwen.json", "{}")
            write_file(package_root / "state" / "openclaw.json", "{}")
            write_file(package_root / "state" / "tasks" / "runs.sqlite", "sqlite")
            write_file(package_root / "state" / "workspace" / "memory" / "memory.json", "{}")

            result = audit_portable_package(package_root)

            self.assertEqual(
                result.unexpected_state_paths,
                ["state/openclaw.json", "state/tasks", "state/workspace"],
            )
            self.assertIn("Package contains mutable state entries that should not be released.", result.warnings)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audit_reports_prune_candidates_by_risk_group(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_file(package_root / "runtime" / "openclaw" / "dist" / "entry.js", "keep")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "entry.js.map", "map")
            write_file(package_root / "runtime" / "openclaw" / "README.md", "markdown")
            write_file(package_root / "runtime" / "openclaw" / "docs" / "reference" / "templates" / "AGENTS.md", "template")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "types.d.ts", "types")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "server.ts", "ts")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "module.mts", "mts")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "script.cts", "cts")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "entry.test.js", "test")
            write_file(package_root / "runtime" / "openclaw" / "dist" / "__tests__" / "fixture.js", "fixture")

            result = audit_portable_package(package_root)
            groups = {group.name: group for group in result.prune_candidates}

            self.assertEqual(groups["source_maps"].risk, "low")
            self.assertEqual(groups["source_maps"].total_files, 1)
            self.assertEqual(groups["source_maps"].total_bytes, 3)
            self.assertEqual(groups["markdown_docs"].total_files, 1)
            self.assertNotIn("runtime/openclaw/docs/reference/templates/AGENTS.md", groups["markdown_docs"].sample_paths)
            self.assertEqual(groups["type_declarations"].total_files, 1)
            self.assertEqual(groups["typescript_sources"].risk, "medium")
            self.assertEqual(groups["typescript_sources"].total_files, 3)
            self.assertNotIn("runtime/openclaw/dist/types.d.ts", groups["typescript_sources"].sample_paths)
            self.assertEqual(groups["test_artifacts"].total_files, 2)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_outputs_json_report_for_package_root(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_file(package_root / "version.json", "{}")

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "audit-portable-package.py"),
                    "--package-root",
                    str(package_root),
                    "--top",
                    "2",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            document = json.loads(completed.stdout)
            self.assertEqual(document["package_root"], str(package_root))
            self.assertEqual(document["total_files"], 1)
            self.assertIn("OpenClawLauncher.exe", document["required_paths_missing"])
            self.assertEqual(document["unexpected_state_paths"], [])
            self.assertIn("prune_candidates", document)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
