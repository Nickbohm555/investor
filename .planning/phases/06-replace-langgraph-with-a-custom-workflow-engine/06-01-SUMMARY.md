---
phase: 06-replace-langgraph-with-a-custom-workflow-engine
plan: 01
subsystem: database
tags: [workflow-engine, alembic, persistence, testing]
requires:
  - phase: 04-hitl-and-broker-prestage
    provides: approval and broker-prestage status vocabulary
provides:
  - app-owned workflow engine contract with persisted-step vocabulary
  - merged Alembic head above the phase 5 branch split
  - workflow and persistence tests anchored to phase 6 contracts
affects: [workflow-engine, migrations, persistence-tests, approvals]
tech-stack:
  added: []
  patterns:
    - thin workflow-engine adapter ahead of persisted runtime cutover
    - explicit Alembic head assertions in persistence tests
key-files:
  created:
    - app/workflows/__init__.py
    - app/workflows/engine.py
    - app/workflows/state.py
    - app/db/migrations/versions/0003_merge_phase5_heads.py
  modified:
    - app/graph/workflow.py
    - app/db/migrations/versions/0002_add_schedule_fields.py
    - tests/graph/test_workflow.py
    - tests/services/test_persistence.py
key-decisions:
  - "Phase 6 locks the public workflow API now with WorkflowEngine.start_run and WorkflowEngine.advance_run, even before database-backed dispatch lands."
  - "Approval outcomes now use final persisted-step vocabulary: awaiting_review, broker_prestaged, and rejected."
  - "The existing 0002 schedule migration had to move to batch mode so the merged Alembic history can execute on SQLite during tests."
patterns-established:
  - "Workflow unit tests assert against serialized state payloads owned by app/workflows rather than runtime resume commands."
  - "Persistence tests build a RevisionMap from imported migration modules and verify the repo exposes one Alembic head."
requirements-completed: [SC-01, SC-02]
duration: 18min
completed: 2026-03-31
---

# Phase 06 Plan 01 Summary

**Phase 6 now has a stable app-owned workflow engine API, final step vocabulary, and one merged Alembic head that upgrades cleanly in tests.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-31T20:03:00Z
- **Completed:** 2026-03-31T20:21:30Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `WorkflowEngine`, `WorkflowEvent`, and `WorkflowResult` as the phase-wide workflow contract the rest of the cutover will target.
- Reworked workflow behavior and unit tests around `awaiting_review`, `broker_prestaged`, and `rejected`, removing runtime resume-command assertions.
- Merged the duplicate phase-5 Alembic heads and added persistence coverage that proves the merged history reaches a single head and still creates the runtime tables.

## Task Commits

Each task was committed atomically:

1. **Task 1: Introduce the app-owned workflow engine contract and update unit coverage** - `c0435e6` (`feat`)
2. **Task 2: Merge the duplicate Alembic heads and prove the branch shape in persistence tests** - `7c5a683` (`test`)

## Files Created/Modified

- `app/workflows/engine.py` - thin phase-bridge engine exposing `start_run` and `advance_run`
- `app/workflows/state.py` - workflow event literal and serialized result container
- `app/workflows/__init__.py` - workflow package exports
- `app/graph/workflow.py` - updated approval/rejection outcomes to phase-6 status vocabulary
- `tests/graph/test_workflow.py` - engine contract and status-step assertions
- `app/db/migrations/versions/0003_merge_phase5_heads.py` - merge revision above both `0002` branches
- `app/db/migrations/versions/0002_add_schedule_fields.py` - batch-mode constraint migration so SQLite upgrade tests pass
- `tests/services/test_persistence.py` - merged-head and upgrade-path assertions

## Decisions Made

- Used an in-memory pause store inside `WorkflowEngine` as a temporary bridge so plan 01 can lock the public API without prematurely designing persisted dispatch.
- Serialized workflow test assertions through `state_payload` to match the app-owned engine contract the next plan will persist into `runs`.
- Treated the SQLite-incompatible Alembic constraint change as a blocking migration defect and fixed it immediately so the merged history can be proven, not just declared.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched the schedule-field migration to Alembic batch mode**
- **Found during:** Task 2
- **Issue:** `0002_add_schedule_fields` used direct constraint alteration, which made the merged migration history fail on SQLite before the new merge revision could be verified.
- **Fix:** Rewrote the migration to use `op.batch_alter_table("runs")` for both upgrade and downgrade.
- **Files modified:** `app/db/migrations/versions/0002_add_schedule_fields.py`
- **Verification:** `python -m pytest tests/services/test_persistence.py -q`
- **Committed in:** `7c5a683`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to make the planned Alembic merge verifiable on the repo’s supported local test database. No scope creep beyond the migration proof path.

## Issues Encountered

- The local Python environment was missing `alembic`, so task verification initially failed during test collection. Installing the declared dependency resolved that environment issue and allowed the migration tests to run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The next plan can remove `thread_id` and move workflow advancement onto stored run state without changing the public engine API again.
- The migration history now has one head and a working SQLite proof path, which lowers the risk of the schema cutover.

---
*Phase: 06-replace-langgraph-with-a-custom-workflow-engine*
*Completed: 2026-03-31*
