---
phase: 06
slug: replace-langgraph-with-a-custom-workflow-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 9.0.2 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/graph/test_workflow.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run the plan-local smoke command from the task `<verify>` block
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Task-smoke feedback latency:** <=30 seconds
- **Wave/full-suite latency:** may exceed 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | SC-01 | unit | `python -m pytest tests/graph/test_workflow.py -q` | ✅ | ⬜ pending |
| 06-01-02 | 01 | 1 | SC-01 | persistence | `python -m pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 2 | SC-01, SC-02 | persistence | `python -m pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 06-02-02 | 02 | 2 | SC-01, SC-02 | unit + persistence | `python -m pytest tests/graph/test_workflow.py tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 06-03-01 | 03 | 3 | SC-02 | api | `python -m pytest tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 06-03-02 | 03 | 3 | SC-02, SC-03 | api + integration | `python -m pytest tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q` | ✅ | ⬜ pending |
| 06-04-01 | 04 | 4 | SC-01, SC-03 | ops | `python -m pytest tests/ops/test_dry_run.py -q` | ✅ | ⬜ pending |
| 06-04-02 | 04 | 4 | SC-01, SC-03 | ops + docs | `python -m pytest tests/ops/test_operational_docs.py tests/ops/test_dry_run.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_persistence.py` — add migration-path coverage for upgrading a Phase-5 schema into the Phase-6 schema, including the duplicate-`0002` Alembic branch situation
- [ ] `tests/services/test_persistence.py` — fence pre-cutover runs into `archived_pre_phase6` / `approval_status=archived` with a `phase6_cutover` payload marker during migration
- [ ] `tests/graph/test_workflow.py` — replace LangGraph-era assertions on `resume_command`, `resuming`, and checkpointer semantics with engine-step assertions
- [ ] `tests/integration/test_hitl_resume.py` — assert approval and rejection advance persisted workflow steps directly instead of replaying a paused payload
- [ ] `tests/api/test_routes.py` — assert the HTTP layer uses `workflow_engine` and exposes no `thread_id`
- [ ] `tests/api/test_routes.py` — assert archived pre-cutover runs return HTTP 410 with the exact cutover rejection detail
- [ ] `tests/integration/test_broker_prestage.py` — assert the approve path consumes returned `handoff` data and persists broker artifacts after restart

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Local upgrade guidance removes LangGraph operator steps cleanly | SC-01 | Requires reading docs and env migration text rather than only runtime assertions | Confirm `README.md` and `.env.example` no longer mention `INVESTOR_LANGGRAPH_CHECKPOINTER_URL`, and verify the documented setup path still matches the FastAPI app entrypoints and cron scripts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Commit-time smoke commands stay under ~15 seconds each
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
