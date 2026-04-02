---
phase: 17-harden-live-run-approval-observability-and-replay-operations
plan: 01
subsystem: database
tags: [operations, observability, sqlalchemy, alembic, redaction]
requires:
  - phase: 16-deepen-quiver-signal-coverage-and-agent-evaluation
    provides: richer research payloads and persisted run context
provides:
  - operation event ORM model and migration
  - repository-backed event writes and reads
  - centralized secret masking for persisted event detail
affects: [phase-17, operations, runtime-observability, replay]
tech-stack:
  added: []
  patterns: [typed operation-event ledger, repository-backed persistence, centralized secret redaction]
key-files:
  created: [app/db/migrations/versions/0005_phase17_operation_events.py]
  modified: [app/db/models.py, app/repositories/operation_events.py, app/services/operation_events.py, tests/services/test_operation_events.py]
key-decisions:
  - "Kept operation-event writes in a dedicated repository/service seam so later runtime instrumentation can stay thin."
  - "Applied secret masking before persistence, not at read time, so durable event detail never stores raw credentials."
patterns-established:
  - "Provider-stage outcomes now persist as first-class rows keyed by run_id and ordered newest-first."
  - "Operation-event detail uses one masking helper fed by the existing settings secret contract."
requirements-completed: [OPS-01]
duration: 12min
completed: 2026-04-02
---

# Phase 17: Harden Live-Run Approval, Observability, And Replay Operations Summary

**Durable operation-event rows with exact stage/provider/outcome fields, newest-first queries, and centralized secret masking**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-04-02
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added failing service coverage that locked the exact operation-event API, persistence fields, masking token, and ordering contract.
- Added `OperationEventRecord` plus an Alembic migration so provider-stage events have a dedicated durable table instead of disappearing into free-form run payloads.
- Implemented repository and service helpers that mask configured secrets before persistence and return per-run events newest first.

## Task Commits

1. **Task 1: Write the failing operation-event persistence and redaction tests** - `55a0fa8` (`test`)
2. **Task 2: Implement the operation-event model, migration, repository, and service** - `a9acb39` (`feat`)

## Files Created/Modified

- `app/db/models.py` - added the `OperationEventRecord` ORM model and typed columns
- `app/db/migrations/versions/0005_phase17_operation_events.py` - created the `operation_events` table migration
- `app/repositories/operation_events.py` - added create/list repository helpers with descending event order
- `app/services/operation_events.py` - added masking-aware write and read helpers
- `tests/services/test_operation_events.py` - locked persistence, redaction, and ordering behavior

## Decisions Made

- Persisted masked detail strings instead of raw values so future operator tools cannot accidentally read secrets back from the database.
- Kept this plan limited to the persistence seam; runtime instrumentation remains for later plans that can depend on a stable event contract.

## Evidence

- `PYTHONPATH=. pytest tests/services/test_operation_events.py -q`
- `rg -n "operation_events|OperationEventRecord|\\*\\*\\*redacted\\*\\*\\*" app/db/models.py app/db/migrations/versions/0005_phase17_operation_events.py app/services/operation_events.py`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- A transient `.git/index.lock` blocked the Task 2 commit once; the lock was already gone by the time I checked, and the retry committed cleanly.

## Next Phase Readiness

- Phase 17 now has a stable persistence seam for provider-stage observability.
- Plan `17-02` can instrument Quiver, LLM, SMTP, approval, and broker boundaries against this shared event service without inventing new storage formats.

---
*Phase: 17-harden-live-run-approval-observability-and-replay-operations*
*Completed: 2026-04-02*
