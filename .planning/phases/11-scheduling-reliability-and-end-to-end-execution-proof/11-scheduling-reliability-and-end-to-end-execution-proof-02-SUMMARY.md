---
phase: 11-scheduling-reliability-and-end-to-end-execution-proof
plan: 02
subsystem: execution
tags: [execution, alpaca, routes, workflow, ops]
requires:
  - phase: 04-03
    provides: broker prestage artifacts and approval handoff flow
provides:
  - explicit execution-confirmation HTTP route
  - token-gated order submission surface
  - durable per-artifact submission checkpointing
  - dry-run submitted-order proof
affects: [api, config, workflow, broker, ops, testing]
tech-stack:
  added: []
  patterns: [two-step approval then execute flow, broker-artifact-backed submission, token-gated execution route, per-artifact reconciliation checkpointing, dry-run JSON proof]
key-files:
  created: [tests/api/test_execution_confirmation.py, tests/tools/test_alpaca_orders.py]
  modified: [app/api/routes.py, app/config.py, app/main.py, app/ops/dry_run.py, app/tools/alpaca.py, app/workflows/engine.py, app/workflows/state.py, tests/conftest.py, tests/integration/test_scheduled_submission_flow.py]
key-decisions:
  - "Keep approval and submission as separate operator-visible steps: approval prestages broker drafts, then POST /runs/{run_id}/execute performs the actual submission."
  - "Use persisted broker artifact records as the source of truth for submission payloads instead of rebuilding orders from ad hoc request input."
  - "Gate execution confirmation behind a dedicated repo-configured trigger token instead of exposing submission on an open run-id route."
  - "Checkpoint each broker artifact before and after submission so partial broker failures stop in a reconciliation-required state rather than silently resubmitting."
patterns-established:
  - "WorkflowEngine.advance_run(...) now owns the broker_prestaged -> submitted transition and persists submitted-order evidence on run state."
  - "Execution confirmation writes `submission_in_flight` / `submitted` artifact statuses so retries are safe by default."
  - "The repo-local dry run exercises scheduled trigger, approval, and execute in one JSON-emitting path."
requirements-completed: [SC11-02]
duration: 5min
completed: 2026-03-31
---

# Phase 11: Scheduling Reliability And End-To-End Execution Proof Summary

**Explicit execution confirmation now advances approved runs from broker drafts to submitted Alpaca orders through repo-owned seams**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-31T20:57:11-04:00
- **Completed:** 2026-03-31T21:01:36-04:00
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Added `POST /runs/{run_id}/execute` so operator confirmation is a distinct repo-owned step after approval/prestage and requires a dedicated execution token.
- Extended the workflow engine to submit persisted broker artifacts, checkpoint progress per artifact, and record `submitted_orders` plus `submitted_order_count`.
- Added an Alpaca `submit_order(...)` adapter and updated the dry-run CLI output to expose execution confirmation results and submitted client order IDs.
- Added regression coverage for unauthorized execute attempts and partial-broker-failure reconciliation behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing route, adapter, and dry-run tests for explicit execution confirmation** - `0b1d7c2` (test)
2. **Task 2: Implement explicit execution confirmation, Alpaca submission, and dry-run submitted-order proof** - `0c03537` (feat)

## Files Created/Modified
- `tests/api/test_execution_confirmation.py` - Verifies successful submission, invalid-state rejection, and idempotent execute behavior.
- `tests/tools/test_alpaca_orders.py` - Verifies Alpaca order submission payload shape and endpoint.
- `tests/ops/test_dry_run.py` - Requires submitted-order proof in dry-run JSON.
- `app/api/routes.py` - Adds the explicit execute route and maps lifecycle failures to `409`.
- `app/config.py` - Adds the dedicated execution trigger token setting.
- `app/workflows/engine.py` - Submits persisted broker artifacts and records submitted-state evidence.
- `app/tools/alpaca.py` - Adds the `/v2/orders` submission wrapper.
- `app/ops/dry_run.py` - Executes the new route and prints submission proof fields.
- `app/main.py` - Shares the configured Alpaca client factory with the workflow engine.
- `app/workflows/state.py` - Extends the workflow event union with `execution:confirm`.
- `tests/conftest.py` - Provides a default execution trigger token in test settings.
- `tests/integration/test_scheduled_submission_flow.py` - Sends the execute token header through the scheduled end-to-end proof.

## Decisions Made
- Submission uses stored broker artifact rows so client order IDs, order shape, and broker policy snapshots stay aligned with the prestage step.
- Execution confirmation remains an explicit second action instead of silently submitting during approval.
- A partial broker submission failure leaves the run in a reconciliation-required state instead of rolling back to a resubmittable clean slate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Shared the configured Alpaca client factory with the workflow engine**
- **Found during:** Task 2 (Implement explicit execution confirmation, Alpaca submission, and dry-run submitted-order proof)
- **Issue:** The existing app wiring only injected the broker client factory into the prestage service, so execution confirmation had no way to use repo-configured doubles or the production Alpaca client.
- **Fix:** Threaded `alpaca_client_factory` through `create_app(...)` into `WorkflowEngine(...)` and used it for `execution:confirm`.
- **Files modified:** `app/main.py`, `app/workflows/engine.py`
- **Verification:** `python -m pytest tests/api/test_execution_confirmation.py tests/tools/test_alpaca_orders.py tests/ops/test_dry_run.py -q`
- **Committed in:** `0c03537`

**2. [Rule 2 - Missing Critical] Added authentication and durable partial-failure handling to the execute route**
- **Found during:** Post-implementation code review
- **Issue:** The initial execute route was unauthenticated, and a mid-loop broker failure could have left externally submitted orders rolled back in local state and eligible for resubmission.
- **Fix:** Added `execution_trigger_token` header validation, per-artifact `submission_in_flight` / `submitted` checkpointing, and regression tests for unauthorized calls plus reconciliation-required failure handling.
- **Files modified:** `app/api/routes.py`, `app/config.py`, `app/ops/dry_run.py`, `app/workflows/engine.py`, `tests/api/test_execution_confirmation.py`, `tests/conftest.py`, `tests/integration/test_scheduled_submission_flow.py`
- **Verification:** `python -m pytest tests/api/test_execution_confirmation.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_dry_run.py -q` and `python -m pytest -q`
- **Committed in:** `9db1b41`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** The deviations kept the new execute step on the same broker seam already used by prestage and added the safety controls required for a submission endpoint.

## Issues Encountered
- The first implementation pass left a syntax error in `app/workflows/engine.py`; this was corrected before the green verification run and did not change the intended behavior.
- Code review surfaced an unauthenticated execute route and a partial-failure resubmission risk. Both were fixed before final verification.

## User Setup Required

None for repo-local verification. Real broker credentials remain optional for later paper-trading smoke tests.

## Next Phase Readiness
- The repo now proves approval-to-submission behavior locally through HTTP routes, workflow state, and dry-run JSON output.
- The remaining merged-scope work is the end-to-end scheduled integration proof and the separate schedule-config hardening plan.

---
*Phase: 11-scheduling-reliability-and-end-to-end-execution-proof*
*Completed: 2026-03-31*
