---
phase: 1
slug: durable-workflow-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/api/test_routes.py tests/services/test_persistence.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/test_routes.py tests/services/test_persistence.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | RUNT-01 | integration | `pytest tests/services/test_persistence.py tests/graph/test_workflow.py -q` | ✅ | ⬜ pending |
| 01-01-02 | 01 | 1 | RUNT-02 | integration | `pytest tests/services/test_persistence.py tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 01-02-01 | 02 | 2 | RUNT-01 | api | `pytest tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 01-02-02 | 02 | 2 | RUNT-03 | api | `pytest tests/api/test_routes.py tests/services/test_tokens.py -q` | ✅ | ⬜ pending |
| 01-03-01 | 03 | 3 | RUNT-01 | integration | `pytest tests/api/test_routes.py tests/services/test_persistence.py tests/graph/test_workflow.py -q` | ✅ | ⬜ pending |
| 01-03-02 | 03 | 3 | RUNT-02 | integration | `pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 01-03-03 | 03 | 3 | RUNT-03 | api | `pytest tests/api/test_routes.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_persistence.py` — add restart-safe run persistence and repository coverage for `RUNT-01` and `RUNT-02`
- [ ] `tests/api/test_routes.py` — add approval error-path coverage for invalid, expired, stale, and duplicate approvals for `RUNT-03`
- [ ] `tests/graph/test_workflow.py` — add same-thread resume coverage across trigger and approval lifecycle for `RUNT-01`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Restart the app between trigger and approval while preserving the same persisted run | RUNT-01 | Full process restart with the production-style app lifecycle is not fully represented by the current automated suite | Start the app, trigger a run, stop the process, restart it with the same database, approve the same run, and confirm the run completes without creating a new run |
| Inspect Postgres rows for runs, recommendations, approval events, and transitions after a completed approval flow | RUNT-02 | The exact persisted schema and row lineage should be spot-checked against the database during early rollout | Execute a full trigger-to-approval flow, query the database tables directly, and confirm one run is associated with recommendation rows, approval events, and transition history |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
