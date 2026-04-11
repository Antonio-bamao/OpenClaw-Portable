# Runtime Stability Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable runtime stability verification tool that runs multiple cold starts and restarts against a portable package and emits a structured JSON report.

**Architecture:** Introduce a focused `runtime_stability` service that orchestrates isolated verification runs over the existing runtime/controller stack and summarizes results. Keep the CLI thin: parse arguments, invoke the service, print or write JSON, and never mutate product defaults or release assets.

**Tech Stack:** Python 3, `unittest`, standard library `argparse`, `json`, `tempfile`, `pathlib`, existing `PortablePaths`, `LauncherController`, and runtime adapter logic.

---

### Task 1: Define the verification result model

**Files:**
- Create: `tests/test_runtime_stability.py`
- Create: `launcher/services/runtime_stability.py`

- [ ] **Step 1: Write the failing test**

Add a test that defines fake per-run outcomes and asserts the service returns a summary plus run records:

```python
def test_verifier_summarizes_cold_and_restart_runs(self) -> None:
    runner = FakeRunner(
        cold_results=[
            {"ok": True, "elapsed": 31.2, "port": 18789, "health_ok": True},
            {"ok": True, "elapsed": 28.4, "port": 18790, "health_ok": True},
        ],
        restart_results=[
            {"ok": True, "elapsed": 12.1, "port": 18790, "health_ok": True},
        ],
    )
    verifier = RuntimeStabilityVerifier(runner=runner)

    result = verifier.verify(package_root=Path("demo"), cold_runs=2, restart_runs=1)

    assert result.summary.all_passed is True
    assert result.summary.cold_runs_passed == 2
    assert result.summary.restart_runs_passed == 1
    assert round(result.summary.max_elapsed_seconds, 2) == 31.20
    assert len(result.runs) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: import failure for `launcher.services.runtime_stability`.

- [ ] **Step 3: Write minimal implementation**

Create `launcher/services/runtime_stability.py` with:

```python
@dataclass(frozen=True)
class RuntimeStabilityRun:
    kind: str
    index: int
    ok: bool
    elapsed_seconds: float
    port: int | None
    health_ok: bool
    error: str
    stdout_log: str
    stderr_log: str


@dataclass(frozen=True)
class RuntimeStabilitySummary:
    all_passed: bool
    cold_runs_passed: int
    restart_runs_passed: int
    max_elapsed_seconds: float
    avg_elapsed_seconds: float


@dataclass(frozen=True)
class RuntimeStabilityResult:
    package_root: Path
    runtime_mode: str
    cold_runs_requested: int
    restart_runs_requested: int
    summary: RuntimeStabilitySummary
    runs: list[RuntimeStabilityRun]
```

and a verifier shell:

```python
class RuntimeStabilityVerifier:
    def __init__(self, runner) -> None:
        self._runner = runner

    def verify(self, *, package_root: Path, cold_runs: int, restart_runs: int) -> RuntimeStabilityResult:
        runs: list[RuntimeStabilityRun] = []
        for index in range(1, cold_runs + 1):
            runs.append(self._runner.run_cold_start(index=index, package_root=package_root))
        for index in range(1, restart_runs + 1):
            runs.append(self._runner.run_restart(index=index, package_root=package_root))
        return build_runtime_stability_result(
            package_root=package_root,
            runtime_mode="openclaw",
            cold_runs_requested=cold_runs,
            restart_runs_requested=restart_runs,
            runs=runs,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: the new summary test passes.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_runtime_stability.py launcher/services/runtime_stability.py
git commit -m "feat: scaffold runtime stability verifier"
```

### Task 2: Cover failure recording and JSON serialization

**Files:**
- Modify: `tests/test_runtime_stability.py`
- Modify: `launcher/services/runtime_stability.py`

- [ ] **Step 1: Write the failing test**

Add a test that verifies failed runs keep the error and log paths and that `to_dict()` is JSON-friendly:

```python
def test_failed_run_keeps_error_and_log_paths(self) -> None:
    failed = RuntimeStabilityRun(
        kind="cold_start",
        index=1,
        ok=False,
        elapsed_seconds=90.0,
        port=None,
        health_ok=False,
        error="runtime did not become healthy in time",
        stdout_log="C:/tmp/out.log",
        stderr_log="C:/tmp/err.log",
    )
    result = build_runtime_stability_result(
        package_root=Path("demo"),
        runtime_mode="openclaw",
        cold_runs_requested=1,
        restart_runs_requested=0,
        runs=[failed],
    )

    document = result.to_dict()

    assert document["summary"]["allPassed"] is False
    assert document["runs"][0]["error"] == "runtime did not become healthy in time"
    assert document["runs"][0]["stderrLog"] == "C:/tmp/err.log"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: attribute error or key mismatch because `to_dict()` is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Add `to_dict()` helpers:

```python
def to_dict(self) -> dict[str, object]:
    return {
        "kind": self.kind,
        "index": self.index,
        "ok": self.ok,
        "elapsedSeconds": round(self.elapsed_seconds, 2),
        "port": self.port,
        "healthOk": self.health_ok,
        "error": self.error,
        "stdoutLog": self.stdout_log,
        "stderrLog": self.stderr_log,
    }
```

and:

```python
def build_runtime_stability_result(...):
    elapsed_values = [run.elapsed_seconds for run in runs]
    cold_passed = sum(1 for run in runs if run.kind == "cold_start" and run.ok)
    restart_passed = sum(1 for run in runs if run.kind == "restart" and run.ok)
    summary = RuntimeStabilitySummary(
        all_passed=all(run.ok for run in runs) if runs else True,
        cold_runs_passed=cold_passed,
        restart_runs_passed=restart_passed,
        max_elapsed_seconds=max(elapsed_values, default=0.0),
        avg_elapsed_seconds=(sum(elapsed_values) / len(elapsed_values)) if elapsed_values else 0.0,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: summary + serialization tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_runtime_stability.py launcher/services/runtime_stability.py
git commit -m "feat: serialize runtime stability results"
```

### Task 3: Add the real runner with isolated temp roots

**Files:**
- Modify: `tests/test_runtime_stability.py`
- Modify: `launcher/services/runtime_stability.py`
- Modify: `launcher/core/paths.py`

- [ ] **Step 1: Write the failing test**

Add a test that verifies the runner builds isolated paths outside the package root:

```python
def test_runner_uses_isolated_temp_state_roots(self) -> None:
    package_root = Path("C:/repo/dist/OpenClaw-Portable")
    factory = RuntimeVerificationPathsFactory(base_temp_root=Path("C:/tmp/checks"))

    created = factory.create(package_root=package_root, run_label="cold-1")

    assert created.project_root != package_root
    assert "checks" in str(created.project_root)
    assert created.state_dir.parent == created.project_root
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: missing factory or mismatched path behavior.

- [ ] **Step 3: Write minimal implementation**

Add a small factory in `launcher/services/runtime_stability.py`:

```python
class RuntimeVerificationPathsFactory:
    def __init__(self, base_temp_root: Path | None = None) -> None:
        self._base_temp_root = base_temp_root

    def create(self, *, package_root: Path, run_label: str) -> PortablePaths:
        root = (self._base_temp_root or (Path(tempfile.gettempdir()) / "OpenClawPortableVerification")) / run_label
        return PortablePaths.for_root(root, temp_base=root / "system-temp")
```

and copy only the minimum package files needed for verification:

```python
def stage_verification_root(source_root: Path, target_root: Path) -> None:
    shutil.copytree(source_root / "runtime", target_root / "runtime", dirs_exist_ok=True)
    shutil.copytree(source_root / "assets", target_root / "assets", dirs_exist_ok=True)
    shutil.copytree(source_root / "tools", target_root / "tools", dirs_exist_ok=True)
    shutil.copytree(source_root / "state" / "provider-templates", target_root / "state" / "provider-templates", dirs_exist_ok=True)
    shutil.copy2(source_root / "version.json", target_root / "version.json")
    shutil.copy2(source_root / "README.txt", target_root / "README.txt")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: isolated-path test passes.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_runtime_stability.py launcher/services/runtime_stability.py launcher/core/paths.py
git commit -m "feat: isolate runtime stability verification roots"
```

### Task 4: Wire the CLI

**Files:**
- Modify: `tests/test_runtime_stability.py`
- Create: `scripts/verify-portable-runtime-stability.py`
- Modify: `launcher/services/runtime_stability.py`

- [ ] **Step 1: Write the failing test**

Add a subprocess CLI test that invokes the new script with a fake package root and monkeypatch-friendly service entrypoint:

```python
def test_cli_writes_json_report(self) -> None:
    completed = subprocess.run(
        [
            "python",
            str(Path.cwd() / "scripts" / "verify-portable-runtime-stability.py"),
            "--package-root",
            str(package_root),
            "--cold-runs",
            "1",
            "--restart-runs",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    document = json.loads(completed.stdout)
    assert document["coldRunsRequested"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: script missing.

- [ ] **Step 3: Write minimal implementation**

Create `scripts/verify-portable-runtime-stability.py`:

```python
def main() -> int:
    args = build_parser().parse_args()
    verifier = build_runtime_stability_verifier()
    result = verifier.verify(
        package_root=Path(args.package_root),
        cold_runs=args.cold_runs,
        restart_runs=args.restart_runs,
        timeout_seconds=args.timeout_seconds,
    )
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_runtime_stability -v
```

Expected: CLI test passes.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_runtime_stability.py scripts/verify-portable-runtime-stability.py launcher/services/runtime_stability.py
git commit -m "feat: add runtime stability verification cli"
```

### Task 5: Manual real-runtime verification and context update

**Files:**
- Modify: `.context/work-log.md`
- Modify: `.context/current-status.md`
- Modify: `.context/task-breakdown.md`

- [ ] **Step 1: Run full automated tests**

Run:

```powershell
python -m unittest discover -s tests
```

Expected: full suite passes.

- [ ] **Step 2: Run a real stability check**

Run:

```powershell
python .\scripts\verify-portable-runtime-stability.py --package-root dist\OpenClaw-Portable --cold-runs 3 --restart-runs 2
```

Expected: JSON output with `summary`, `runs`, and log paths. If a run fails, capture the exact error and leave the result in the report rather than hiding it.

- [ ] **Step 3: Verify package state was not polluted**

Run:

```powershell
python .\scripts\audit-portable-package.py --top 5
```

Expected: no new package-root `state/` pollution introduced by the stability verification script itself.

- [ ] **Step 4: Update project context**

Record:

- the new verifier tool
- real cold-start / restart timing summary
- any failure modes found
- whether logs were sufficient

- [ ] **Step 5: Validate context**

Run:

```powershell
python C:\Users\m1591\.codex\skills\project-context-os\scripts\validate_context.py --project-root .
```

Expected: `context is valid`
