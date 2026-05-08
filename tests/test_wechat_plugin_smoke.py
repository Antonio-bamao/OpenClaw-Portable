from __future__ import annotations

import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from launcher.services.wechat_plugin_smoke import (
    detect_wechat_register_failure,
    find_wechat_plugin_root,
    verify_wechat_plugin_smoke_prerequisites,
)


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"wechat-plugin-smoke-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def write_minimal_package(package_root: Path, *, manifest_name: str = "openclaw") -> None:
    runtime_root = package_root / "runtime" / "openclaw"
    plugin_root = package_root / "state" / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin"
    (runtime_root / "dist" / "plugins" / "runtime").mkdir(parents=True, exist_ok=True)
    (runtime_root / "dist" / "plugins" / "runtime" / "index.js").write_text("export function createPluginRuntime() {}\n", encoding="utf-8")
    (runtime_root / "package.json").write_text(json.dumps({"name": manifest_name, "bin": {"openclaw": "openclaw.mjs"}}), encoding="utf-8")
    (plugin_root / "dist").mkdir(parents=True, exist_ok=True)
    (plugin_root / "dist" / "index.js").write_text("export default {}\n", encoding="utf-8")
    (package_root / "state" / "runtime").mkdir(parents=True, exist_ok=True)
    (package_root / "state" / "runtime" / "openclaw.json").write_text(json.dumps({"gateway": {"mode": "local"}}), encoding="utf-8")


class WechatPluginSmokeTests(unittest.TestCase):
    def test_prerequisites_accept_packaged_state_npm_plugin_and_full_runtime_manifest(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_minimal_package(package_root)

            missing = verify_wechat_plugin_smoke_prerequisites(package_root)

            self.assertEqual(missing, [])
            self.assertEqual(find_wechat_plugin_root(package_root), package_root / "state" / "npm" / "node_modules" / "@tencent-weixin" / "openclaw-weixin")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_prerequisites_reject_plugin_sdk_shim_as_runtime_manifest(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_minimal_package(package_root, manifest_name="")
            (package_root / "runtime" / "openclaw" / "package.json").write_text(
                json.dumps({"type": "module", "exports": {"./plugin-sdk/*": "./plugin-sdk/*.js"}}),
                encoding="utf-8",
            )

            missing = verify_wechat_plugin_smoke_prerequisites(package_root)

            self.assertIn("runtime/openclaw/package.json:name=openclaw", missing)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_register_failure_marker_detection_is_specific_to_gateway_register(self) -> None:
        self.assertTrue(detect_wechat_register_failure("openclaw-weixin failed during register: Error: Unable to resolve plugin runtime module"))
        self.assertFalse(detect_wechat_register_failure("weixin getUpdates error (1/3): TypeError: fetch failed"))

    def test_cli_can_run_prerequisite_check_without_starting_gateway(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            package_root = temp_dir / "OpenClaw-Portable"
            write_minimal_package(package_root)

            completed = subprocess.run(
                [
                    "python",
                    str(Path.cwd() / "scripts" / "verify-wechat-plugin-runtime.py"),
                    "--package-root",
                    str(package_root),
                    "--prerequisites-only",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            document = json.loads(completed.stdout)
            self.assertTrue(document["ok"])
            self.assertEqual(document["missing"], [])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
