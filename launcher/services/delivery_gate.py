from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from launcher.services.portable_audit import audit_portable_package
from launcher.services.release_assets import build_release_asset_name, read_package_version
from launcher.services.runtime_stability import RuntimeStabilityVerifier, build_runtime_stability_verifier


PASSED = "passed"
FAILED = "failed"
PENDING = "pending"
SKIPPED = "skipped"


@dataclass(frozen=True)
class DeliveryGateCheck:
    name: str
    status: str
    message: str
    details: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class DeliveryGateResult:
    status: str
    package_root: Path
    release_dir: Path
    checks: list[DeliveryGateCheck]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "packageRoot": str(self.package_root),
            "releaseDir": str(self.release_dir),
            "checks": [check.to_dict() for check in self.checks],
        }


def verify_delivery_flow(
    *,
    package_root: Path,
    release_dir: Path,
    stability_verifier: RuntimeStabilityVerifier | None = None,
    cold_runs: int = 0,
    restart_runs: int = 0,
    runtime_mode: str = "openclaw",
    timeout_seconds: float | None = None,
    feishu_e2e_evidence: Path | None = None,
    removable_media_path: Path | None = None,
    av_evidence: Path | None = None,
) -> DeliveryGateResult:
    package_root = package_root.resolve()
    release_dir = release_dir.resolve()
    checks = [
        _check_portable_audit(package_root),
        _check_release_assets(package_root=package_root, release_dir=release_dir),
        _check_runtime_stability(
            package_root=package_root,
            stability_verifier=stability_verifier,
            cold_runs=cold_runs,
            restart_runs=restart_runs,
            runtime_mode=runtime_mode,
            timeout_seconds=timeout_seconds,
        ),
        _check_evidence(
            name="feishu-private-chat-e2e",
            evidence_path=feishu_e2e_evidence,
            pending_message="Real Feishu private-chat E2E still needs actual Feishu app credentials and network access.",
        ),
        _check_evidence(
            name="removable-media-run",
            evidence_path=removable_media_path,
            pending_message="Real U-disk read/write and cold-start measurement needs a mounted delivery medium.",
        ),
        _check_evidence(
            name="multi-engine-av-smartscreen",
            evidence_path=av_evidence,
            pending_message="Local Defender baseline does not replace SmartScreen reputation or multi-engine AV evidence.",
        ),
    ]
    return DeliveryGateResult(
        status=_aggregate_status(checks),
        package_root=package_root,
        release_dir=release_dir,
        checks=checks,
    )


def _check_portable_audit(package_root: Path) -> DeliveryGateCheck:
    try:
        audit = audit_portable_package(package_root, top_limit=8)
    except Exception as exc:  # noqa: BLE001
        return DeliveryGateCheck("portable-package-audit", FAILED, str(exc), {})

    blocking_items: list[str] = []
    if audit.required_paths_missing:
        blocking_items.append(f"missing required paths: {', '.join(audit.required_paths_missing)}")
    if audit.unexpected_state_paths:
        blocking_items.append(f"unexpected release state: {', '.join(audit.unexpected_state_paths)}")
    if audit.write_risk_directories:
        blocking_items.append(f"write-risk directories: {', '.join(audit.write_risk_directories)}")
    remaining_prune_groups = [group for group in audit.prune_candidates if group.total_files > 0]
    if remaining_prune_groups:
        blocking_items.append(
            "remaining prune candidates: "
            + ", ".join(f"{group.name}={group.total_files}" for group in remaining_prune_groups)
        )

    status = FAILED if blocking_items else PASSED
    message = "; ".join(blocking_items) if blocking_items else "Portable package audit passed."
    return DeliveryGateCheck(
        "portable-package-audit",
        status,
        message,
        {
            "totalMb": round(audit.total_bytes / (1024 * 1024), 2),
            "totalFiles": audit.total_files,
            "warnings": audit.warnings,
        },
    )


def _check_release_assets(*, package_root: Path, release_dir: Path) -> DeliveryGateCheck:
    try:
        version = read_package_version(package_root)
    except Exception as exc:  # noqa: BLE001
        return DeliveryGateCheck("release-assets", FAILED, str(exc), {})

    expected_archive = release_dir / build_release_asset_name(version)
    expected_update_json = release_dir / "update.json"
    expected_package_files = [package_root / "update-manifest.json", package_root / "update-signature.json"]
    missing = [str(path) for path in [expected_archive, expected_update_json, *expected_package_files] if not path.exists()]
    if missing:
        return DeliveryGateCheck("release-assets", FAILED, f"Missing release assets: {', '.join(missing)}", {"version": version})

    archive_missing = _find_missing_archive_entries(expected_archive, package_root.name)
    if archive_missing:
        return DeliveryGateCheck(
            "release-assets",
            FAILED,
            f"Release zip is missing required entries: {', '.join(archive_missing)}",
            {"version": version, "archive": str(expected_archive)},
        )

    try:
        document = json.loads(expected_update_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return DeliveryGateCheck("release-assets", FAILED, f"update.json is not valid JSON: {exc}", {"version": version})
    if str(document.get("version") or "") != version:
        return DeliveryGateCheck(
            "release-assets",
            FAILED,
            f"update.json version does not match package version {version}.",
            {"version": version, "updateJsonVersion": document.get("version")},
        )

    return DeliveryGateCheck(
        "release-assets",
        PASSED,
        "Release zip, update.json, manifest, and signature are present.",
        {"version": version, "archive": str(expected_archive), "updateJson": str(expected_update_json)},
    )


def _find_missing_archive_entries(archive_path: Path, package_root_name: str) -> list[str]:
    required_entries = [
        f"{package_root_name}/version.json",
        f"{package_root_name}/update-manifest.json",
        f"{package_root_name}/update-signature.json",
    ]
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile:
        return [f"{archive_path} is not a valid zip file"]
    return [entry for entry in required_entries if entry not in names]


def _check_runtime_stability(
    *,
    package_root: Path,
    stability_verifier: RuntimeStabilityVerifier | None,
    cold_runs: int,
    restart_runs: int,
    runtime_mode: str,
    timeout_seconds: float | None,
) -> DeliveryGateCheck:
    if cold_runs <= 0 and restart_runs <= 0:
        return DeliveryGateCheck("runtime-stability", SKIPPED, "Runtime stability check skipped by run counts.", {})
    verifier = stability_verifier or build_runtime_stability_verifier()
    try:
        result = verifier.verify(
            package_root=package_root,
            cold_runs=max(cold_runs, 0),
            restart_runs=max(restart_runs, 0),
            runtime_mode=runtime_mode,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        return DeliveryGateCheck("runtime-stability", FAILED, str(exc), {})
    if not result.summary.all_passed:
        return DeliveryGateCheck("runtime-stability", FAILED, "Runtime stability verification failed.", result.to_dict())
    return DeliveryGateCheck("runtime-stability", PASSED, "Runtime stability verification passed.", result.to_dict())


def _check_evidence(*, name: str, evidence_path: Path | None, pending_message: str) -> DeliveryGateCheck:
    if evidence_path is None:
        return DeliveryGateCheck(name, PENDING, pending_message, {})
    if not evidence_path.exists():
        return DeliveryGateCheck(name, FAILED, f"Evidence path does not exist: {evidence_path}", {"path": str(evidence_path)})
    return DeliveryGateCheck(name, PASSED, "Evidence path exists.", {"path": str(evidence_path)})


def _aggregate_status(checks: list[DeliveryGateCheck]) -> str:
    statuses = [check.status for check in checks]
    if FAILED in statuses:
        return FAILED
    if PENDING in statuses:
        return PENDING
    return PASSED
