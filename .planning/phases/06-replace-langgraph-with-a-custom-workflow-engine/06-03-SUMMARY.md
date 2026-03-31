---
phase: 06-replace-langgraph-with-a-custom-workflow-engine
plan: 03
subsystem: api
tags: [fastapi, approvals, broker-prestage, integration]
requires:
  - phase: 06-replace-langgraph-with-a-custom-workflow-engine
    provides: persisted workflow engine and phase 6 run schema
provides:
  - trigger routes wired to workflow_engine
  - approval and rejection through persisted workflow events
  - archived-run HTTP 410 contract
affects: [api-routes, approvals, integration-tests, app-composition]
tech-stack:
  added: []
  patterns:
    - FastAPI app state owns workflow_engine instead of runtime
    - approval service advances persisted workflow events before broker prestage
key-files:
  created: []
  modified:
    - app/main.py
    - app/api/routes.py
    - app/services/approvals.py
    - app/services/run_service.py
    - tests/conftest.py
    - tests/api/test_routes.py
    - tests/integration/test_hitl_resume.py
key-decisions:
  - "Trigger routes continue to return status=started while the persisted run itself moves to awaiting_review."
  - "Archived pre-phase6 runs fail with a fixed 410 detail instead of attempting partial compatibility."
patterns-established:
  - "HTTP approval handling records the approval event and then advances the persisted workflow engine."
  - "Restart-safe integration tests recreate the app against the same database and assert persisted-step transitions directly."
requirements-completed: [SC-02, SC-03]
duration: 14min
completed: 2026-03-31
---

# Phase 06 Plan 03 Summary

**FastAPI trigger and approval paths now run entirely through the persisted workflow engine, with restart-safe broker-prestage behavior preserved after app recreation.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-31T20:37:00Z
- **Completed:** 2026-03-31T20:51:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Replaced `app.state.runtime` with `app.state.workflow_engine` in app composition and trigger routes.
- Cut approval/rejection over to `workflow_engine.advance_run(...)`, removing thread-id and resume-path expectations from API and integration tests.
- Added a fixed HTTP 410 contract for archived pre-phase6 runs while keeping restart-safe broker artifact creation green.

## Task Commits

The route and approval tasks overlapped heavily in the same files, so they were committed as one focused integration change:

1. **Tasks 1-2: Route and approval workflow-engine cutover with restart-safe integration coverage** - `44bca9c` (`feat`)

## Files Created/Modified

- `app/main.py` - app-state composition now exposes `workflow_engine`
- `app/api/routes.py` - trigger and approval routes wired to persisted workflow events
- `app/services/approvals.py` - approval handling through `advance_run()` with archived-run guard
- `app/services/run_service.py` - recommendation normalization for serialized engine payloads
- `tests/conftest.py` - persisted-run fixture no longer expects thread identifiers
- `tests/api/test_routes.py` - archived-run 410 contract and threadless route assertions
- `tests/integration/test_hitl_resume.py` - persisted-step transition assertions

## Decisions Made

- Kept the HTTP response contract stable (`status: started`) while letting the stored run move independently to `awaiting_review`.
- Treated archived pre-cutover rows as a stale 410 path rather than a special-case approval branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Normalized serialized recommendation payloads before persistence**
- **Found during:** Route cutover verification
- **Issue:** The workflow engine now stores serialized recommendation dicts, but `RunService.store_recommendations()` still assumed model instances and crashed during trigger execution.
- **Fix:** Added recommendation-input normalization for dict, `Recommendation`, and `CandidateRecommendation` shapes.
- **Files modified:** `app/services/run_service.py`
- **Verification:** `python -m pytest tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q`
- **Committed in:** `44bca9c`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for the engine serialization change to flow through the route layer cleanly. No scope creep beyond compatibility work.

## Issues Encountered

- The first route wiring pass surfaced a mismatch between serialized workflow payloads and the recommendation-persistence helper. Normalizing the input shapes fixed the issue without changing the external route contract.

## User Setup Required

None.

## Next Phase Readiness

- The repo can now remove the final LangGraph dependency and operator-facing terminology without reopening runtime behavior.
- Restart-safe trigger, approval, rejection, and broker-prestage flows are all green on the persisted engine path.

---
*Phase: 06-replace-langgraph-with-a-custom-workflow-engine*
*Completed: 2026-03-31*
