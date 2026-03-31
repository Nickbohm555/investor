---
phase: 01-durable-workflow-foundation
plan: 01
subsystem: database
tags: [sqlalchemy, postgres, persistence, runtime, testing]
requires: []
provides:
  - durable run tables with thread and audit state
  - repository methods for run, recommendation, approval, and transition writes
  - service-layer transaction boundaries for persisted run lifecycle updates
affects: [phase-01-plan-02, phase-01-plan-03, runtime, testing]
tech-stack:
  added: []
  patterns: [repository-service split, cached default engine with injectable test factories]
key-files:
  created: [app/repositories/run_repository.py, app/services/run_service.py]
  modified: [app/config.py, app/db/models.py, app/db/migrations/versions/0001_create_run_tables.py, app/db/session.py, tests/services/test_persistence.py]
key-decisions:
  - "Separate ORM business records from future workflow checkpoint persistence so run state writes stay app-owned and queryable."
  - "Cache only the default SQLAlchemy engine; explicit test database URLs create fresh engines to avoid leaking in-memory state across runs."
patterns-established:
  - "Repository methods own row-level persistence while RunService owns transaction scopes."
  - "Persistence tests use injected session factories backed by ephemeral SQLite engines."
requirements-completed: [RUNT-01, RUNT-02]
duration: 5min
completed: 2026-03-31
---

# Phase 01: durable-workflow-foundation Summary

**Durable run tables, repository writes, and transaction-owning services now persist run, recommendation, approval, and transition state outside process memory**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-31T01:25:21-04:00
- **Completed:** 2026-03-31T01:30:20-04:00
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Expanded the runtime schema with stable `thread_id`, approval metadata, transition reasons, and audit timestamps.
- Added `RunRepository` and `RunService` so durable run lifecycle writes happen inside explicit transaction scopes.
- Extended persistence tests to cover schema shape, service lifecycle behavior, and duplicate approval-event protection.

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand the runtime persistence schema for durable run state** - `bea3196` (feat)
2. **Task 2: Add repository and service contracts for durable run lifecycle writes** - `2296ccd` (feat)

## Files Created/Modified
- `app/config.py` - Adds durable runtime settings for the checkpointer URL and approval-token TTL.
- `app/db/models.py` - Expands durable run, recommendation, approval-event, and transition tables.
- `app/db/migrations/versions/0001_create_run_tables.py` - Aligns the initial migration with the expanded runtime schema.
- `app/db/session.py` - Keeps the default engine reusable while preserving injectable test session factories.
- `app/repositories/run_repository.py` - Implements persisted CRUD and lifecycle logging for runs and child records.
- `app/services/run_service.py` - Provides transaction-owning run lifecycle methods for later runtime orchestration.
- `tests/services/test_persistence.py` - Verifies schema, service lifecycle writes, and duplicate approval protection.

## Decisions Made
- Separate application-owned runtime records from future LangGraph checkpoint persistence so run audit data stays straightforward to query and validate.
- Cache only the default configured engine. Explicit database URLs used in tests create fresh engines so isolated runs do not share in-memory SQLite state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced Python 3.10 union syntax with Python 3.9-compatible annotations**
- **Found during:** Task 1 (Expand the runtime persistence schema for durable run state)
- **Issue:** `str | None` annotations broke import-time execution under the repo's Python 3.9 environment.
- **Fix:** Switched to `Optional[...]` annotations in the new settings and ORM fields.
- **Files modified:** `app/config.py`, `app/db/models.py`
- **Verification:** `pytest tests/services/test_persistence.py -q`
- **Committed in:** `bea3196`

**2. [Rule 3 - Blocking] Narrowed SQLAlchemy engine caching to prevent SQLite memory leakage across tests**
- **Found during:** Task 2 (Add repository and service contracts for durable run lifecycle writes)
- **Issue:** Caching engines by explicit in-memory SQLite URLs caused later tests to reuse the same database and violate unique constraints.
- **Fix:** Cached only the default configured engine and returned fresh engines for explicitly supplied database URLs.
- **Files modified:** `app/db/session.py`
- **Verification:** `pytest tests/services/test_persistence.py -q`
- **Committed in:** `2296ccd`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required for the planned persistence layer to run correctly in this repo. No scope creep.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The durable schema and service boundary are ready for runtime invoke/resume wiring in `01-02`.
- Approval-token validation and actual LangGraph resume behavior are still pending the next plan.

---
*Phase: 01-durable-workflow-foundation*
*Completed: 2026-03-31*
