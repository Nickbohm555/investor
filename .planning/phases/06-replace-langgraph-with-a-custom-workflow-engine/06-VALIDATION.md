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
| **Quick run command** | `python -m pytest tests/graph/test_workflow.py tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/graph/test_workflow.py tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 0 | SC-01 | migration + integration | `python -m pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 1 | SC-01 | unit + integration | `python -m pytest tests/graph/test_workflow.py tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 06-03-01 | 03 | 1 | SC-02 | integration | `python -m pytest tests/integration/test_hitl_resume.py tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 06-04-01 | 04 | 2 | SC-01, SC-03 | integration + ops | `python -m pytest tests/integration/test_broker_prestage.py tests/ops/test_dry_run.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_persistence.py` — add migration-path coverage for upgrading a Phase-5 schema into the Phase-6 schema, including the duplicate-`0002` Alembic branch situation
- [ ] `tests/graph/test_workflow.py` — replace LangGraph-era assertions on `resume_command`, `resuming`, and checkpointer semantics with engine-step assertions
- [ ] `tests/integration/test_hitl_resume.py` — assert approval and rejection advance persisted workflow steps directly instead of replaying a paused payload

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
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
