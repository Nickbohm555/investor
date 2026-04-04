---
phase: 20-direct-post-triggered-research-to-email-run-path
plan: 01
subsystem: api
tags: [manual-trigger, api, workflow, testing]
requires:
  - phase: 03-scheduling-reliability-and-end-to-end-execution-proof
    provides: scheduled trigger route and persisted workflow start pattern
provides:
  - manual trigger failure contract
  - manual trigger route coverage
  - manual trigger integration coverage
affects: [phase-20, api, workflow]
tech-stack:
  added: []
  patterns: [manual trigger error mapping, route-level observability, route-to-email integration test]
key-files:
  created: [tests/api/test_manual_trigger.py, tests/integration/test_manual_trigger_email_flow.py]
  modified: [app/api/routes.py]
key-decisions:
  - "Keep Phase 20 on the existing POST /runs/trigger route and change only its observability and failure payload."
  - "Preserve the created run record on workflow startup failure and return its run_id to the operator."
patterns-established:
  - "Manual trigger success now logs manual_trigger result=started run_id=%s before returning HTTP 202."
  - "Manual trigger startup failures now log manual_trigger result=failure run_id=%s and return a structured HTTP 500 detail payload."
requirements-completed: [PH20-01]
duration: 18min
completed: 2026-04-03
---

# Phase 20: Direct POST-triggered research-to-email run path Summary

**Locked the direct manual POST route contract with dedicated API and integration coverage, plus operator-visible failure payloads that preserve the created run id**

## Performance

- **Duration:** 18 min
- **Completed:** 2026-04-03
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added route-level tests for successful direct manual POSTs and workflow-start failures after run creation.
- Added integration coverage proving a manual `POST /runs/trigger` sends one memo and persists the run at `awaiting_review`.
- Updated the manual route to log explicit success and failure outcomes and return `{"message": "Manual trigger failed", "run_id": ...}` on startup failure.

## Task Commits

1. **Task 1: Create red tests for the direct manual trigger contract** - `25a8642` (test)
2. **Task 2: Implement manual route observability and failure response details** - `6250cc4` (feat)

## Files Created/Modified

- `tests/api/test_manual_trigger.py` - covers successful manual POSTs and structured failure responses that expose the created run id
- `tests/integration/test_manual_trigger_email_flow.py` - proves one manual POST sends one memo and persists awaiting-review state
- `app/api/routes.py` - maps manual trigger startup failures to operator-visible HTTP 500 detail payloads and adds route logging

## Decisions Made

- Reused the existing manual trigger route rather than introducing any new operator-specific API surface.
- Kept the run id generation, pending-run creation, and baseline-report lookup unchanged so only the failure semantics and observability moved.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The route already satisfied the success contract, so the red step isolated only the missing structured 500 response and logging behavior.

## User Setup Required

None for this plan. Live manual proof still depends on real app, Quiver, LLM, and SMTP configuration in later plans.

## Next Phase Readiness

- Plan 20-01 is complete and exposes a stable manual route contract that the live-proof CLI can call directly.
- Plan 20-02 can now focus on staged preflight diagnostics and the operator-facing `trigger-manual` helper without needing additional API changes.

---
*Phase: 20-direct-post-triggered-research-to-email-run-path*
*Completed: 2026-04-03*
