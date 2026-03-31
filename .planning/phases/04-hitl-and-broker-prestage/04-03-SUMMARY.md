---
phase: 04-hitl-and-broker-prestage
plan: 03
subsystem: api
tags: [approvals, broker, integration, restart-safety, testing]
requires:
  - phase: 04-01
    provides: durable approval service and persisted-thread resume behavior
  - phase: 04-02
    provides: broker artifact persistence and deterministic prestage policy validation
provides:
  - approval-to-broker prestage wiring with broker_prestaged route status
  - restart-safe integration coverage for approve, reject, duplicate, and invalid broker-policy flows
affects: [api, broker, workflow, testing]
tech-stack:
  added: []
  patterns: [approval-resume then prestage sequencing, local stubbed external-service fixtures]
key-files:
  created: [tests/integration/test_broker_prestage.py]
  modified: [app/main.py, app/api/routes.py, app/services/approvals.py, tests/conftest.py, tests/api/test_routes.py, tests/integration/test_hitl_resume.py, tests/integration/test_durable_workflow.py]
key-decisions:
  - "Run broker prestage after the durable approval transition commits so restart-safe approval semantics survive and SQLite does not deadlock on nested writes."
  - "Expose broker-prestage completion explicitly as broker_prestaged instead of overloading completed, so route and integration tests can distinguish approval-only success from broker-ready success."
patterns-established:
  - "Test app composition defaults to local mail and Alpaca stubs unless a test overrides them explicitly."
  - "Approval-to-broker integration is proven by recreating the app against the same database before the callback fires."
requirements-completed: [HITL-01, HITL-02, BRKR-01, BRKR-02, BRKR-03]
duration: 14min
completed: 2026-03-31
---

# Phase 04: HITL And Broker Prestage Summary

**Approved runs now resume the persisted workflow, prestage traceable Alpaca-ready broker artifacts, and expose restart-safe approve, reject, duplicate, and invalid-policy behavior through end-to-end tests**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-31T15:10:48Z
- **Completed:** 2026-03-31T15:25:11Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added shared Phase 4 persisted-run and stubbed external-service fixtures so restart-safe route and integration tests can recreate the app across approval callbacks.
- Wired the approval service and app composition into the broker prestage layer, returning `broker_prestaged` after successful prestage and rejecting invalid broker-policy paths without creating artifacts.
- Added end-to-end integration coverage proving broker artifacts are created and linked correctly on approve, skipped on reject, blocked on invalid policy, and still protected by duplicate/stale approval semantics.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add shared persisted-run fixtures and route-level Phase 4 assertions** - `30e9e98` (test)
2. **Task 2: Wire approve into broker prestage and add end-to-end approval-to-broker integration coverage** - `945ad4b` (feat)

## Files Created/Modified
- `app/main.py` - Composes the broker prestage service into the app state and supports injected mail and Alpaca test doubles.
- `app/api/routes.py` - Injects prestage behavior into approval handling and maps broker-policy failures to explicit 409 responses.
- `app/services/approvals.py` - Sequences durable approval, workflow resume, and broker prestage into a `broker_prestaged` terminal path.
- `tests/conftest.py` - Adds persisted Phase 4 fixtures and default local test doubles for SMTP and Alpaca.
- `tests/api/test_routes.py` - Verifies the approval endpoint returns `broker_prestaged` and preserves 404, 409, and 410 semantics.
- `tests/integration/test_hitl_resume.py` - Verifies approve transitions through `resuming` into `broker_prestaged` while reject remains side-effect free.
- `tests/integration/test_broker_prestage.py` - Verifies approve creates broker artifacts, reject creates none, and invalid policy blocks persistence.
- `tests/integration/test_durable_workflow.py` - Verifies restart-safe approval now ends in `broker_prestaged`.

## Decisions Made
- Treated `broker_prestaged` as the externally visible success contract for approved runs so the system can distinguish broker-ready state from generic completion.
- Kept the app test harness local-first by defaulting `app_factory` to stub mail and Alpaca clients, with explicit overrides for targeted integration cases.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split approval and prestage into separate transactions**
- **Found during:** Task 2 (Wire approve into broker prestage and add end-to-end approval-to-broker integration coverage)
- **Issue:** Calling the broker artifact persistence layer from inside the approval transaction caused SQLite database-lock failures during restart-safe integration tests.
- **Fix:** Committed the durable approval transition first, ran resume/prestage outside that write transaction, then opened a second transaction for the final `broker_prestaged` status update.
- **Files modified:** `app/services/approvals.py`
- **Verification:** `python -m pytest tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py tests/api/test_routes.py -q`
- **Committed in:** `945ad4b`

**2. [Rule 3 - Blocking] Defaulted test app composition to local SMTP and Alpaca stubs**
- **Found during:** Task 2 (Wire approve into broker prestage and add end-to-end approval-to-broker integration coverage)
- **Issue:** Existing integration tests that used `app_factory` without explicit overrides attempted real SMTP or Alpaca calls once Phase 4 composition was added.
- **Fix:** Updated the shared test fixture layer to inject local mail and Alpaca doubles unless a test passes an explicit override.
- **Files modified:** `tests/conftest.py`, `tests/api/test_routes.py`
- **Verification:** `python -m pytest -q`
- **Committed in:** `945ad4b`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were necessary to keep the full approval-to-broker flow restart-safe and locally testable. No scope creep.

## Issues Encountered
None

## User Setup Required

None - Phase 4 stays within application-owned draft artifacts and local test doubles. No new external setup steps were introduced here.

## Next Phase Readiness
- Phase 4 is complete: approve, reject, duplicate, stale, and invalid-policy flows are covered end to end with persisted broker artifact traceability.
- Phase 5 can focus on operational readiness, environment validation, dry-run tooling, and final launch documentation.

---
*Phase: 04-hitl-and-broker-prestage*
*Completed: 2026-03-31*
