---
phase: 1
slug: durable-workflow-foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `pytest tests/api/test_routes.py tests/services/test_persistence.py tests/graph/test_workflow.py -q` |
| **Postgres smoke command** | `docker compose up -d postgres && INVESTOR_DATABASE_URL=postgresql://investor:investor@localhost:5432/investor INVESTOR_LANGGRAPH_CHECKPOINTER_URL=postgresql://investor:investor@localhost:5432/investor pytest tests/integration/test_durable_workflow.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~45 seconds with Postgres smoke |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/test_routes.py tests/services/test_persistence.py tests/graph/test_workflow.py -q`
- **After every plan wave:** Run `pytest -q`
- **After Plan 03 tasks:** Run `docker compose up -d postgres && INVESTOR_DATABASE_URL=postgresql://investor:investor@localhost:5432/investor INVESTOR_LANGGRAPH_CHECKPOINTER_URL=postgresql://investor:investor@localhost:5432/investor pytest tests/integration/test_durable_workflow.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | RUNT-01 | persistence | `pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 01-01-02 | 01 | 1 | RUNT-02 | persistence | `pytest tests/services/test_persistence.py -q` | ✅ | ⬜ pending |
| 01-02-01 | 02 | 2 | RUNT-01,RUNT-02 | runtime/bootstrap | `python -c "import tomllib, pathlib; data = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); deps = data['project']['dependencies']; required = {'langgraph', 'langgraph-checkpoint-postgres', 'psycopg[binary]'}; missing = required.difference(deps); assert not missing, missing; from langgraph.checkpoint.postgres import PostgresSaver; print(PostgresSaver.__name__)" && pytest tests/graph/test_workflow.py tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 01-02-02 | 02 | 2 | RUNT-03 | api | `pytest tests/api/test_routes.py -q` | ✅ | ⬜ pending |
| 01-03-01 | 03 | 3 | RUNT-01,RUNT-02 | integration | `pytest tests/integration/test_durable_workflow.py tests/api/test_routes.py -q && docker compose up -d postgres && INVESTOR_DATABASE_URL=postgresql://investor:investor@localhost:5432/investor INVESTOR_LANGGRAPH_CHECKPOINTER_URL=postgresql://investor:investor@localhost:5432/investor pytest tests/integration/test_durable_workflow.py -q` | ✅ | ⬜ pending |
| 01-03-02 | 03 | 3 | RUNT-02,RUNT-03 | integration/api | `pytest tests/services/test_persistence.py tests/api/test_routes.py tests/integration/test_durable_workflow.py -q && docker compose up -d postgres && INVESTOR_DATABASE_URL=postgresql://investor:investor@localhost:5432/investor INVESTOR_LANGGRAPH_CHECKPOINTER_URL=postgresql://investor:investor@localhost:5432/investor pytest tests/integration/test_durable_workflow.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/services/test_persistence.py` — every plan task now has an explicit `<automated>` command, so no MISSING verification scaffold remains
- [x] `tests/api/test_routes.py` — approval error-path coverage is assigned to concrete plan tasks `01-02-02` and `01-03-02`
- [x] `tests/graph/test_workflow.py` — same-thread resume and runtime bootstrap coverage are assigned to plan task `01-02-01`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Restart the app between trigger and approval while preserving the same persisted run | RUNT-01 | Full process restart with the production-style app lifecycle is not fully represented by the current automated suite | Start the app, trigger a run, stop the process, restart it with the same database, approve the same run, and confirm the run completes without creating a new run |
| Inspect Postgres rows for runs, recommendations, approval events, and transitions after a completed approval flow | RUNT-02 | The exact persisted schema and row lineage should be spot-checked against the database during early rollout | Execute a full trigger-to-approval flow, query the database tables directly, and confirm one run is associated with recommendation rows, approval events, and transition history |

## Residual Risk

- The phase now requires an automated Postgres smoke command, but the executor must still document any failure to bring up local Postgres or initialize the LangGraph Postgres checkpointer in the summary rather than silently falling back to SQLite-only confidence.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Runtime dependency imports verified against `pyproject.toml`
- [ ] Postgres smoke command executed or explicitly called out as residual risk
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
