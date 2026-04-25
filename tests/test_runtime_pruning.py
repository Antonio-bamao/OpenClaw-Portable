import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from launcher.services.runtime_pruning import prune_runtime_tree


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"runtime-pruning-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


class RuntimePruningTests(unittest.TestCase):
    def test_prunes_verified_candidate_groups_by_default(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            runtime_root.mkdir(parents=True, exist_ok=True)
            (runtime_root / "dist").mkdir(parents=True, exist_ok=True)
            (runtime_root / "docs").mkdir(parents=True, exist_ok=True)
            (runtime_root / "docs" / "reference" / "templates").mkdir(parents=True, exist_ok=True)
            (runtime_root / "dist" / "__tests__").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native" / "test").mkdir(parents=True, exist_ok=True)
            (runtime_root / "dist" / "entry.js").write_text("console.log('ok')\n", encoding="utf-8")
            (runtime_root / "dist" / "entry.js.map").write_text("{}", encoding="utf-8")
            (runtime_root / "docs" / "README.md").write_text("# docs\n", encoding="utf-8")
            (runtime_root / "docs" / "reference" / "templates" / "AGENTS.md").write_text("# template\n", encoding="utf-8")
            (runtime_root / "dist" / "types.d.ts").write_text("export interface Demo {}\n", encoding="utf-8")
            (runtime_root / "dist" / "server.ts").write_text("export {};\n", encoding="utf-8")
            (runtime_root / "dist" / "server.mts").write_text("export {};\n", encoding="utf-8")
            (runtime_root / "dist" / "feature.spec.js").write_text("describe('spec', () => {})\n", encoding="utf-8")
            (runtime_root / "dist" / "__tests__" / "fixture.js").write_text("fixture\n", encoding="utf-8")
            (runtime_root / "native" / "test" / "helper.cc").write_text("// helper\n", encoding="utf-8")
            (runtime_root / "package.json").write_text("{}", encoding="utf-8")

            result = prune_runtime_tree(runtime_root)

            self.assertEqual(result.files_removed, 8)
            self.assertGreater(result.bytes_freed, 0)
            self.assertFalse((runtime_root / "dist" / "entry.js.map").exists())
            self.assertFalse((runtime_root / "docs" / "README.md").exists())
            self.assertFalse((runtime_root / "dist" / "types.d.ts").exists())
            self.assertFalse((runtime_root / "dist" / "server.ts").exists())
            self.assertFalse((runtime_root / "dist" / "server.mts").exists())
            self.assertFalse((runtime_root / "dist" / "feature.spec.js").exists())
            self.assertFalse((runtime_root / "dist" / "__tests__" / "fixture.js").exists())
            self.assertFalse((runtime_root / "native" / "test" / "helper.cc").exists())
            self.assertTrue((runtime_root / "docs" / "reference" / "templates" / "AGENTS.md").exists())
            self.assertTrue((runtime_root / "dist" / "entry.js").exists())
            self.assertTrue((runtime_root / "package.json").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_supports_dry_run_without_deleting_files(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            runtime_root.mkdir(parents=True, exist_ok=True)
            candidate = runtime_root / "artifact.js.map"
            candidate.write_text("{}", encoding="utf-8")

            result = prune_runtime_tree(runtime_root, dry_run=True)

            self.assertEqual(result.files_removed, 1)
            self.assertTrue(candidate.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_script_can_prune_runtime_tree_from_repo_root(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            runtime_root.mkdir(parents=True, exist_ok=True)
            (runtime_root / "artifact.js.map").write_text("{}", encoding="utf-8")
            (runtime_root / "artifact.ts").write_text("export {};\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "prune-portable-runtime.py"),
                    "--runtime-path",
                    str(runtime_root),
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((runtime_root / "artifact.js.map").exists())
            self.assertFalse((runtime_root / "artifact.ts").exists())
            self.assertIn('"files_removed": 2', completed.stdout)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_script_accepts_custom_patterns_without_changing_defaults(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            runtime_root.mkdir(parents=True, exist_ok=True)
            (runtime_root / "notes.md").write_text("# keep defaults out\n", encoding="utf-8")
            (runtime_root / "server.ts").write_text("export {};\n", encoding="utf-8")
            (runtime_root / "server.mts").write_text("export {};\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "prune-portable-runtime.py"),
                    "--runtime-path",
                    str(runtime_root),
                    "--pattern",
                    "*.ts",
                    "--pattern",
                    "*.mts",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((runtime_root / "server.ts").exists())
            self.assertFalse((runtime_root / "server.mts").exists())
            self.assertTrue((runtime_root / "notes.md").exists())
            self.assertIn('"patterns": ["*.ts", "*.mts"]', completed.stdout)
            self.assertIn('"files_removed": 2', completed.stdout)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_supports_directory_name_pruning_for_experiments(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            (runtime_root / "dist" / "__tests__").mkdir(parents=True, exist_ok=True)
            (runtime_root / "docs" / "guides" / "test").mkdir(parents=True, exist_ok=True)
            (runtime_root / "docs" / "contest").mkdir(parents=True, exist_ok=True)
            (runtime_root / "dist" / "__tests__" / "fixture.js").write_text("test fixture\n", encoding="utf-8")
            (runtime_root / "docs" / "guides" / "test" / "run-tests.mdx").write_text("# test docs\n", encoding="utf-8")
            (runtime_root / "docs" / "contest" / "keep.mdx").write_text("# keep me\n", encoding="utf-8")

            result = prune_runtime_tree(runtime_root, directory_names=("__tests__", "test"))

            self.assertEqual(result.files_removed, 2)
            self.assertFalse((runtime_root / "dist" / "__tests__" / "fixture.js").exists())
            self.assertFalse((runtime_root / "docs" / "guides" / "test" / "run-tests.mdx").exists())
            self.assertTrue((runtime_root / "docs" / "contest" / "keep.mdx").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_script_accepts_directory_names_for_test_artifact_experiments(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            runtime_root = temp_dir / "runtime" / "openclaw"
            (runtime_root / "native" / "test").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native" / "contest").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native" / "test" / "helper.cc").write_text("// helper\n", encoding="utf-8")
            (runtime_root / "native" / "contest" / "keep.cc").write_text("// keep\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "prune-portable-runtime.py"),
                    "--runtime-path",
                    str(runtime_root),
                    "--directory-name",
                    "__tests__",
                    "--directory-name",
                    "test",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((runtime_root / "native" / "test" / "helper.cc").exists())
            self.assertTrue((runtime_root / "native" / "contest" / "keep.cc").exists())
            self.assertIn('"files_removed": 1', completed.stdout)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
