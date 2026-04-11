# Runtime Prune Candidate Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add read-only runtime pruning candidate groups to the portable package audit output.

**Architecture:** Extend `launcher/services/portable_audit.py` with a candidate-group dataclass and rule evaluation over the existing file-size map. Keep the CLI unchanged except for the JSON field emitted by `PortablePackageAuditResult.to_dict()`.

**Tech Stack:** Python 3 standard library, `unittest`, `pathlib`, `fnmatch`, dataclasses.

---

### Task 1: Candidate Groups In Audit Output

**Files:**
- Modify: `tests/test_portable_audit.py`
- Modify: `launcher/services/portable_audit.py`

- [ ] **Step 1: Write failing tests**

Add a test that creates a fake runtime tree with `.map`, `.md`, `.d.ts`, `.ts`, `.mts`, `.cts`, `.test.js`, and `__tests__` files, then asserts candidate group names, byte counts, sample paths, and `.d.ts` exclusion from TypeScript sources. Extend the CLI test to assert `prune_candidates` exists.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests.test_portable_audit -v`
Expected: failure because `PortablePackageAuditResult` has no `prune_candidates` field.

- [ ] **Step 3: Implement minimal service changes**

Add `PortablePruneCandidateGroup`, candidate rule helpers, and `prune_candidates` serialization. Reuse `_collect_file_sizes()` so there is no second full tree walk.

- [ ] **Step 4: Run GREEN**

Run: `python -m unittest tests.test_portable_audit -v`
Expected: all tests pass.

- [ ] **Step 5: Verify full suite and real audit**

Run: `python -m unittest discover -s tests`
Run: `python scripts\audit-portable-package.py --top 12`
Expected: full tests pass and real audit JSON includes `prune_candidates`.
