---
phase: 01-durable-workflow-foundation
plan: 02
subsystem: api
tags: [fastapi, langgraph, approvals, runtime, postgres]
requires:
  - phase: 01
    provides: durable run tables and transaction-owning persistence services
provides:
  - durable trigger and approval route wiring backed by persisted run state
  - runtime bootstrap seam for PostgresSaver with signed approval URLs
  - explicit 4xx approval error contracts with persisted approval-event logging
affects: [phase-01-plan-03, runtime, api, testing]
tech-stack:
  added: [langgraph, langgraph-checkpoint-postgres, psycopg[binary]]
  patterns: [composition-root dependency wiring, persisted approval validation before resume]
key-files:
  created: [app/graph/runtime.py]
  modified: [pyproject.toml, app/main.py, app/api/routes.py, app/graph/workflow.py, app/services/tokens.py, app/services/run_service.py, app/db/session.py, tests/api/test_routes.py, tests/graph/test_workflow.py]
key-decisions:
  - "Route handlers persist and validate approval state before calling the runtime resume path, so duplicate and stale callbacks are rejected from database truth instead of transient app memory."
  - "Runtime bootstrap falls back to a no-op checkpointer on non-Postgres URLs so SQLite tests can verify invoke/resume behavior without pretending to be a live checkpoint backend."
patterns-established:
  - "FastAPI app state holds settings, session factory, run service, runtime, and research node as injectable durable dependencies."
  - "Approval tokens are converted into stable token IDs and checked against persisted approval events before resume."
requirements-completed: [RUNT-01, RUNT-02, RUNT-03]
duration: 7min
completed: 2026-03-31
---

# Phase 01: durable-workflow-foundation Summary

**Persisted trigger and approval routes now reuse durable run/thread state, bootstrap the LangGraph saver seam, and return explicit 4xx responses for invalid approval callbacks**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-31T01:33:00-04:00
- **Completed:** 2026-03-31T01:40:25-04:00
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Replaced process-local `workflow_store` usage with app-composed durable dependencies and persisted run lookup on trigger/resume.
- Added `InvestorRuntime` to bootstrap a `PostgresSaver` seam, generate signed approval/rejection URLs, and reuse the same `thread_id` on resume.
- Added explicit approval-domain errors and HTTP mappings for invalid, expired, missing, stale, and duplicate approval attempts, with persisted approval-event logging.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the durable workflow runtime and persisted invoke/resume service path** - `69778dc` (feat)
2. **Task 2: Map approval-domain failures to explicit HTTP responses and persisted audit writes** - `f70782b` (feat)

## Files Created/Modified
- `pyproject.toml` - Adds the durable runtime dependencies required for LangGraph and Postgres checkpoint support.
- `app/main.py` - Composes settings, session factory, run service, runtime, and research dependencies on app startup.
- `app/api/routes.py` - Persists trigger state before invoke and maps approval-domain failures to deliberate HTTP responses.
- `app/graph/runtime.py` - Bootstraps the checkpointer seam, signs approval URLs, and reuses durable thread IDs.
- `app/graph/workflow.py` - Uses runtime-supplied signed approval/rejection URLs instead of raw `run_id:decision` links.
- `app/services/tokens.py` - Returns stable `token_id` values alongside validated approval payloads.
- `app/services/run_service.py` - Validates persisted approval state, records approval events, and logs transitions before resume.
- `app/db/session.py` - Shares in-memory SQLite safely for app tests while preserving injectable engines.
- `tests/api/test_routes.py` - Covers persisted trigger/approval behavior plus 400, 404, 409, and 410 approval responses.
- `tests/graph/test_workflow.py` - Covers signed-link email composition and runtime bootstrap with a patched saver.

## Decisions Made
- Approval state validation happens in the persistence service before runtime resume so route behavior is driven by database truth, not process-local state.
- Non-Postgres URLs use a no-op checkpointer seam in tests. That keeps runtime logic injectable while reserving real saver setup for Postgres-backed environments.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added StaticPool handling for shared in-memory SQLite app tests**
- **Found during:** Task 1 (Build the durable workflow runtime and persisted invoke/resume service path)
- **Issue:** FastAPI route tests opened fresh SQLite memory connections and could not see the created tables.
- **Fix:** Updated engine creation so the shared in-memory SQLite URL uses `StaticPool` and `check_same_thread=False`.
- **Files modified:** `app/db/session.py`
- **Verification:** `pytest tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **Committed in:** `69778dc`

**2. [Rule 3 - Blocking] Used an isolated verification venv for manifest-import proof**
- **Found during:** Task 1 verification
- **Issue:** The local default `python` was 3.9 without `tomllib`, and the global 3.13 interpreter did not have the new LangGraph packages installed.
- **Fix:** Created `.venv-gsd-verify` and used its Python interpreter to verify the manifest dependency import path without mutating the system Python.
- **Files modified:** None (environment-only verification step)
- **Verification:** `./.venv-gsd-verify/bin/python -c "... from langgraph.checkpoint.postgres import PostgresSaver ..."` and `pytest tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **Committed in:** N/A

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to prove the durable runtime wiring and error contracts in this local environment. No product-scope creep.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Trigger and approval behavior now use persisted run/thread state and explicit 4xx contracts, so restart-safe end-to-end coverage can be added in `01-03`.
- Postgres-backed checkpoint smoke still needs to be exercised through the dedicated integration path in the next plan.

---
*Phase: 01-durable-workflow-foundation*
*Completed: 2026-03-31*
