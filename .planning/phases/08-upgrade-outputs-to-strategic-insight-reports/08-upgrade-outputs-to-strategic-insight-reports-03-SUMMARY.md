---
phase: 08-upgrade-outputs-to-strategic-insight-reports
plan: 03
subsystem: workflow
tags: [workflow, routes, persistence, reporting, baseline]
requires:
  - phase: 08-01
    provides: strategic report contract and builder
  - phase: 08-02
    provides: deterministic report renderer and email composition wrapper
provides:
  - baseline-aware strategic report workflow execution
  - persisted strategic report payloads on run state
  - route-level baseline selection from prior delivered runs
affects: [api, workflow, persistence, approvals, testing]
tech-stack:
  added: []
  patterns: [latest-delivered baseline lookup, persisted report payloads, workflow-owned report composition]
key-files:
  created: [tests/graph/test_workflow_reporting.py]
  modified: [app/api/routes.py, app/graph/workflow.py, app/repositories/run_repository.py, app/services/run_service.py, app/workflows/engine.py, tests/api/test_routes.py, tests/graph/test_workflow.py]
key-decisions:
  - "Select the baseline from the most recent completed run with persisted report and finalized outcome data, never from rendered email text."
  - "Persist `strategic_report` and `baseline_run_id` directly on paused workflow state so later review does not need to reconstruct report context."
patterns-established:
  - "Trigger routes query `RunService.get_latest_report_baseline(...)` before workflow execution and pass that baseline into the engine."
  - "Workflow execution builds the strategic report before email delivery and stores the serialized report beside the finalized outcome."
requirements-completed: [REP-01, REP-02, REP-03]
duration: 11min
completed: 2026-03-31
---

# Phase 08: Upgrade Outputs To Strategic Insight Reports Summary

**Baseline-aware workflow execution that builds, emails, and persists strategic insight reports from real prior delivered runs**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-31T21:13:40Z
- **Completed:** 2026-03-31T21:25:10Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added latest-delivered baseline selection in the repository/service layer and threaded it through both manual and scheduled trigger routes.
- Replaced the workflow’s flat memo composition path with strategic report building plus report email rendering.
- Persisted `strategic_report`, `baseline_run_id`, `finalized_outcome`, and rendered `email_body` together so later review and approval flows use the same source of truth.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing workflow and route tests for baseline-aware report generation and persisted report state** - `33839f9` (test)
2. **Task 2: Replace flat memo generation with persisted strategic reports and baseline-aware workflow wiring** - `4f1df48` (feat)

## Files Created/Modified
- `app/repositories/run_repository.py` - Selects the most recent completed run with persisted report/email state as the baseline candidate.
- `app/services/run_service.py` - Exposes baseline lookup that returns only the report/final-outcome data needed for comparison.
- `app/api/routes.py` - Loads baseline report state before manual and scheduled workflow execution.
- `app/workflows/engine.py` - Carries baseline report context into workflow invocation.
- `app/graph/workflow.py` - Builds strategic reports, renders report emails, and persists report/baseline metadata instead of flat memo content.
- `tests/graph/test_workflow.py` - Verifies workflow email output now uses the strategic report headings.
- `tests/graph/test_workflow_reporting.py` - Verifies report persistence and dropped-ticker handling from baseline runs.
- `tests/api/test_routes.py` - Verifies trigger routes persist strategic report state and ignore undelivered runs during baseline selection.

## Decisions Made
- Keep baseline selection in the application persistence layer so manual and scheduled runs follow the same canonical rule.
- Persist the structured report object directly on run state rather than comparing or reconstructing from rendered email text later.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extended `WorkflowEngine.start_run(...)` to accept `baseline_report`**
- **Found during:** Task 2 (Replace flat memo generation with persisted strategic reports and baseline-aware workflow wiring)
- **Issue:** The current repo routes execute through `WorkflowEngine.start_run(...)`, not the runtime call shape assumed by the plan, so there was no existing path to pass baseline state into workflow execution.
- **Fix:** Added an optional `baseline_report` argument to the workflow engine and forwarded it into `CompiledInvestorWorkflow.invoke(...)`.
- **Files modified:** `app/workflows/engine.py`, `app/api/routes.py`
- **Verification:** `python -m pytest tests/graph/test_workflow_reporting.py tests/graph/test_workflow.py tests/api/test_routes.py -q`
- **Committed in:** `4f1df48`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation preserved the planned behavior in the repo’s actual execution architecture without expanding product scope.

## Issues Encountered
- The initial workflow reporting expectation assumed the graph test stub would yield an immediate-action report, but the stub still marked the candidate as broker-ineligible and therefore deferred. Updating the stub to the intended immediate-action scenario restored alignment with the Phase 8 behavior under test.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 8 is complete: live runs now compute strategic insight reports against the latest prior delivered baseline, send the new report sections, and persist the structured report for later review.
- Future work can build on the persisted `strategic_report` contract directly without revisiting memo-era string parsing or baseline derivation.

---
*Phase: 08-upgrade-outputs-to-strategic-insight-reports*
*Completed: 2026-03-31*
