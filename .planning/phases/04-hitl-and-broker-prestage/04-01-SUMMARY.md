---
phase: 04-hitl-and-broker-prestage
plan: 01
subsystem: api
tags: [approvals, hitl, fastapi, workflow, testing]
requires:
  - phase: 01-03
    provides: persisted run records, approval events, and restart-safe runtime resume
provides:
  - durable approval service with explicit duplicate, stale, missing, and not-awaiting-review errors
  - approval route wiring that resumes the persisted thread and exposes stable 404, 409, and 410 semantics
affects: [api, workflow, approvals, testing]
tech-stack:
  added: []
  patterns: [durable approval service, explicit persisted-thread resume branches]
key-files:
  created: [app/repositories/runs.py, app/services/approvals.py, tests/integration/test_hitl_resume.py]
  modified: [app/api/routes.py, app/graph/workflow.py, tests/api/test_routes.py, tests/graph/test_workflow.py]
key-decisions:
  - "Keep approval decision handling in an application-owned service that loads persisted run state and resumes the workflow with the stored thread_id."
  - "Map duplicate and not-awaiting-review decisions to 409, stale terminal decisions to 410, and missing runs to 404 so the callback contract stays explicit."
patterns-established:
  - "Approval callbacks operate on persisted state only and do not rely on transient in-process workflow state."
  - "Workflow resume results include explicit branch metadata so tests can prove approve and reject routing without guessing from side effects."
requirements-completed: [HITL-01, HITL-02]
duration: 7min
completed: 2026-03-31
---

# Phase 04: HITL And Broker Prestage Summary

**Durable approval callbacks now resume the persisted workflow thread with explicit duplicate, stale, and reject semantics proven by route, workflow, and restart-safe integration tests**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-31T14:56:16Z
- **Completed:** 2026-03-31T15:03:03Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added a dedicated approval service and run repository seam that enforce one durable decision per run and resume the stored workflow thread on approve.
- Rewired the approval callback route to the durable service and locked in stable 404, 409, and 410 HTTP mappings.
- Added restart-safe HITL integration coverage plus workflow branch assertions for explicit `broker_prestage` and `rejected` resume behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define the durable approval-decision service and failing HITL coverage** - `bd6c235` (feat)
2. **Task 2: Wire the approval route and workflow resume branch to the durable service** - `11f78a1` (feat)

## Files Created/Modified
- `app/repositories/runs.py` - Repository helpers for persisted run lookup, approval-event dedupe, recommendation lookup, and state transitions.
- `app/services/approvals.py` - Approval service, domain errors, module entry point, and persisted-thread resume logic.
- `app/api/routes.py` - Approval callback wiring and explicit domain-error-to-HTTP mapping.
- `app/graph/workflow.py` - Awaiting-review status normalization and explicit approve/reject resume branch metadata.
- `tests/integration/test_hitl_resume.py` - Restart-safe approval, reject, duplicate, stale, and missing-run integration coverage.
- `tests/api/test_routes.py` - Route-level approval callback assertions for 404, 409, and 410 outcomes.
- `tests/graph/test_workflow.py` - Workflow branch assertions for `broker_prestage` on approve and terminal rejection on reject.

## Decisions Made
- Kept the approval decision service application-owned and session-backed instead of burying the logic inside the route or runtime layer.
- Normalized the review status to `awaiting_review` so the persisted state machine and tests share one explicit vocabulary.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Normalized the persisted review status string**
- **Found during:** Task 1 (Define the durable approval-decision service and failing HITL coverage)
- **Issue:** Existing workflow state used `awaiting_human_review`, which did not match the Phase 4 plan's explicit `awaiting_review` state-machine contract.
- **Fix:** Updated the workflow pause state and related tests to use `awaiting_review`.
- **Files modified:** `app/graph/workflow.py`, `tests/api/test_routes.py`, `tests/graph/test_workflow.py`, `tests/integration/test_hitl_resume.py`
- **Verification:** `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py tests/integration/test_hitl_resume.py -q`
- **Committed in:** `bd6c235`, `11f78a1`

**2. [Rule 3 - Blocking] Reconstructed typed recommendations before resume**
- **Found during:** Task 1 (Define the durable approval-decision service and failing HITL coverage)
- **Issue:** Persisted workflow state stores recommendation objects as JSON dicts, but the existing handoff path expects typed models with `model_dump()`.
- **Fix:** Rehydrated persisted recommendation payloads into `CandidateRecommendation` objects before calling the runtime resume path.
- **Files modified:** `app/services/approvals.py`
- **Verification:** `python -m pytest tests/integration/test_hitl_resume.py -q`
- **Committed in:** `bd6c235`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to make persisted resume behavior match the planned Phase 4 state machine. No scope creep.

## Issues Encountered
None

## User Setup Required

None - no external service configuration changes were needed for the approval durability work.

## Next Phase Readiness
- The approval callback path now operates on persisted state and is safe to extend with broker-prestage behavior.
- Phase 04-02 can build broker artifacts and policy validation on top of a stable approve/reject boundary.

---
*Phase: 04-hitl-and-broker-prestage*
*Completed: 2026-03-31*
