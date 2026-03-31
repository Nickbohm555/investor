---
phase: 06-replace-langgraph-with-a-custom-workflow-engine
plan: 02
subsystem: database
tags: [workflow-engine, schema, persistence, migrations]
requires:
  - phase: 06-replace-langgraph-with-a-custom-workflow-engine
    provides: workflow-engine API and merged Alembic head
provides:
  - phase 6 run schema without thread_id
  - archival fence for pre-cutover runs
  - persisted workflow-engine advancement on RunRecord state
affects: [approvals, routes, persistence-tests, broker-prestage]
tech-stack:
  added: []
  patterns:
    - run.current_step and run.state_payload as the workflow cursor
    - engine advancement from persisted run state instead of in-memory pause maps
key-files:
  created:
    - app/db/migrations/versions/0004_phase6_workflow_engine_schema.py
  modified:
    - app/db/models.py
    - app/repositories/run_repository.py
    - app/repositories/runs.py
    - app/services/run_service.py
    - app/workflows/engine.py
    - tests/graph/test_workflow.py
    - tests/services/test_persistence.py
key-decisions:
  - "Pre-cutover runs are fenced off as archived_pre_phase6 instead of attempting unsafe resume compatibility."
  - "WorkflowEngine now loads and updates runs through the database, with recommendations rehydrated only where needed."
patterns-established:
  - "Schema migrations can archive legacy workflow rows before destructive column removal."
  - "Graph tests seed runs first and then prove engine methods operate from persisted run state."
requirements-completed: [SC-01, SC-02]
duration: 15min
completed: 2026-03-31
---

# Phase 06 Plan 02 Summary

**Run persistence now uses app-owned workflow fields only, and the workflow engine advances from stored run state rather than an in-memory pause map.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-31T20:22:00Z
- **Completed:** 2026-03-31T20:37:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Removed `thread_id` from the `RunRecord` schema and added a phase-6 migration that archives legacy runs before dropping the old column.
- Updated the run-service contract so create and approval paths no longer accept or return `thread_id`.
- Reworked `WorkflowEngine` to load, persist, and advance workflow state directly from the `runs` table.

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace the runtime persistence contract with app-owned workflow fields and migration support** - `9474ce5` (`feat`)
2. **Task 2: Implement the persisted workflow engine core against the new schema** - `b3f189a` (`feat`)

## Files Created/Modified

- `app/db/migrations/versions/0004_phase6_workflow_engine_schema.py` - archives pre-cutover runs and removes `thread_id`
- `app/db/models.py` - final phase-6 run schema
- `app/repositories/run_repository.py` - run creation without thread identifiers
- `app/repositories/runs.py` - state payload persistence helper
- `app/services/run_service.py` - threadless run-service surface
- `app/workflows/engine.py` - persisted workflow start and event advancement
- `tests/services/test_persistence.py` - schema-upgrade archival coverage
- `tests/graph/test_workflow.py` - persisted-engine behavior assertions

## Decisions Made

- Legacy review-time runs are explicitly archived instead of being treated as safe approval-compatible state after the cutover.
- The engine persists serialized workflow payloads on the run row and rehydrates only the recommendation subset needed for approval handoff generation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated `RunRepository` alongside the planned service/repository files**
- **Found during:** Task 1
- **Issue:** `RunService.create_pending_run()` still depended on `RunRepository.create_run(thread_id=...)`, so removing `thread_id` from the service contract was impossible without touching the repository implementation too.
- **Fix:** Removed `thread_id` from `RunRepository.create_run()` and aligned its call sites.
- **Files modified:** `app/repositories/run_repository.py`
- **Verification:** `python -m pytest tests/services/test_persistence.py -q`
- **Committed in:** `9474ce5`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to keep the persistence contract coherent. No extra feature scope was added.

## Issues Encountered

- None after the phase-6 migration and engine behavior were aligned around the stored run row.

## User Setup Required

None - no external setup required.

## Next Phase Readiness

- Trigger and approval routes can now call the workflow engine directly without reintroducing `thread_id`.
- Archived legacy rows already have a clear rejection path for the upcoming HTTP cutover.

---
*Phase: 06-replace-langgraph-with-a-custom-workflow-engine*
*Completed: 2026-03-31*
