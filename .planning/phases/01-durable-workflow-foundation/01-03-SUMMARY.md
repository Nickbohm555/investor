---
phase: 01-durable-workflow-foundation
plan: 03
subsystem: testing
tags: [pytest, integration, restart-safety, postgres, verification]
requires:
  - phase: 01
    provides: durable trigger and approval routes backed by persisted run state
provides:
  - restart-safe integration coverage across app recreation
  - lifecycle persistence assertions for runs, recommendations, approvals, and transitions
  - documented fast and Postgres smoke verification commands
affects: [phase-01-verification, testing, docs]
tech-stack:
  added: []
  patterns: [app-factory fixture for env-isolated app instances, restart-safe integration verification]
key-files:
  created: [tests/integration/test_durable_workflow.py]
  modified: [tests/conftest.py, tests/services/test_persistence.py, README.md, app/db/session.py]
key-decisions:
  - "Integration coverage recreates the app against the same database URL instead of simulating restart state in-memory, so restart safety is tested at the API boundary."
  - "Postgres URLs are normalized to the `psycopg` driver in the session layer so the documented smoke command can use the repo's required URL shape."
patterns-established:
  - "Phase verification combines a fast local suite with a separately documented Postgres smoke path."
  - "Persistent workflow tests inspect approval events and transitions directly from the database, not just HTTP responses."
requirements-completed: [RUNT-01, RUNT-02, RUNT-03]
duration: 4min
completed: 2026-03-31
---

# Phase 01: durable-workflow-foundation Summary

**Restart-safe integration tests, full persisted lifecycle assertions, and repo-level verification commands now prove the durable workflow foundation beyond happy-path units**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T01:42:30-04:00
- **Completed:** 2026-03-31T01:46:51-04:00
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added an integration test that triggers a run, recreates the app, approves the same run, and confirms duplicate approvals are rejected.
- Expanded service-level persistence coverage to assert a completed lifecycle with recommendations, approval events, and ordered state transitions.
- Replaced the generic README verification section with explicit fast-suite and Postgres smoke commands for Phase 1.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add restart-safe integration coverage for persisted invoke and approval** - `a328715` (test)
2. **Task 2: Close persistence and failure-mode coverage gaps in the service and verification docs** - `163d72f` (test)

## Files Created/Modified
- `tests/conftest.py` - Adds an app factory fixture for env-isolated app instances and database overrides.
- `tests/integration/test_durable_workflow.py` - Proves trigger/approve behavior survives app recreation and records durable audit rows.
- `tests/services/test_persistence.py` - Adds a full lifecycle persistence test through `RunService`.
- `README.md` - Documents the fast Phase 1 suite and the Postgres-backed smoke command.
- `app/db/session.py` - Normalizes bare Postgres URLs to the installed `psycopg` driver for the smoke path.

## Decisions Made
- Restart safety is verified by constructing two real app instances against the same database, not by faking resumed state in one process.
- The session layer rewrites bare `postgresql://` URLs to `postgresql+psycopg://` so the repo’s documented environment variables align with the installed driver.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Normalized Postgres URLs to the installed `psycopg` driver**
- **Found during:** Task 2 verification
- **Issue:** The documented smoke command used `postgresql://...`, but SQLAlchemy defaulted that URL to `psycopg2`, which was not available in the local test interpreter.
- **Fix:** Rewrote bare Postgres URLs to `postgresql+psycopg://` in the session factory.
- **Files modified:** `app/db/session.py`
- **Verification:** `pytest tests/services/test_persistence.py tests/api/test_routes.py tests/integration/test_durable_workflow.py -q`
- **Committed in:** `163d72f`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix keeps the documented smoke path aligned with the repo’s declared dependency. No scope creep.

## Issues Encountered
- The documented `docker compose up -d postgres` command could not claim port `5432` on this machine because another service was already bound there.
- Running the Postgres smoke against the existing `localhost:5432` service failed with `password authentication failed for user "investor"`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 1 now has durable runtime wiring plus restart-safe integration coverage and explicit verification commands.
- Residual risk: the exact documented Postgres smoke command was not validated end-to-end on this machine because the existing port-5432 database did not accept the documented `investor/investor` credentials.

---
*Phase: 01-durable-workflow-foundation*
*Completed: 2026-03-31*
