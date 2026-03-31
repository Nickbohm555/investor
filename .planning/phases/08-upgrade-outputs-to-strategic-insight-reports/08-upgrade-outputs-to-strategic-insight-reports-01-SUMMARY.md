---
phase: 08-upgrade-outputs-to-strategic-insight-reports
plan: 01
subsystem: reporting
tags: [reports, pydantic, workflow, testing]
requires:
  - phase: 07-03
    provides: finalized research outcomes with deterministic recommendation branches
provides:
  - typed strategic insight report schema
  - deterministic baseline comparison helpers
  - bucketed report builder for immediate, defer, and research actions
affects: [workflow, email, api, testing]
tech-stack:
  added: []
  patterns: [typed reporting contract, baseline-aware comparison, deterministic action bucketing]
key-files:
  created: [app/schemas/reports.py, app/services/report_compare.py, app/services/report_builder.py, tests/services/test_report_compare.py, tests/services/test_report_builder.py]
  modified: [app/schemas/workflow.py]
key-decisions:
  - "Keep strategic insight as a typed application contract instead of deriving report semantics from prose."
  - "Compare current recommendations against the prior delivered baseline by uppercase ticker before any rendering logic."
patterns-established:
  - "Report rendering consumers should import `StrategicInsightReport` from the workflow schema export surface."
  - "Immediate, defer, and research buckets are assigned in deterministic Python rules rather than prompt-owned branching."
requirements-completed: [REP-01, REP-02]
duration: 6min
completed: 2026-03-31
---

# Phase 08: Upgrade Outputs To Strategic Insight Reports Summary

**Typed strategic report models and deterministic comparison/build logic for immediate, defer, and research action buckets**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-31T20:57:11Z
- **Completed:** 2026-03-31T21:02:45Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added a new `StrategicInsightReport` contract and re-exported it through the existing workflow schema surface.
- Implemented deterministic baseline comparison helpers with exact change labels and dropped-ticker detection.
- Built a strict report builder that classifies recommendations into immediate, defer, and research queues with baseline-aware summary metadata.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests and report-contract skeletons for comparison and bucketed report building** - `05ea0b7` (test)
2. **Task 2: Implement deterministic comparison and report-building logic on the new typed contract** - `68a4bb7` (feat)

**Plan metadata:** `5db78bc` (style)

## Files Created/Modified
- `app/schemas/reports.py` - Defines the typed strategic report contract and bucket-specific item models.
- `app/schemas/workflow.py` - Re-exports `StrategicInsightReport` for downstream workflow and email integrations.
- `app/services/report_compare.py` - Classifies candidate deltas and detects dropped baseline tickers deterministically.
- `app/services/report_builder.py` - Converts current and baseline research outcomes into a validated strategic report object.
- `tests/services/test_report_compare.py` - Pins exact change labels and dropped-ticker behavior.
- `tests/services/test_report_builder.py` - Pins bucket classification, action strings, and baseline-aware summary output.

## Decisions Made
- Keep the report schema strict and typed so later rendering code can consume report data without re-deriving business rules.
- Use uppercase ticker maps and deterministic rule ordering for comparisons so baseline change detection stays stable across runs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched report schema annotations to Python 3.9-compatible typing constructs**
- **Found during:** Task 1 (Write failing tests and report-contract skeletons for comparison and bucketed report building)
- **Issue:** The local test runner evaluates Pydantic model annotations under Python 3.9, which rejected `|` union field annotations in the new schema module at import time.
- **Fix:** Replaced those schema field annotations with `Optional[...]` and `List[...]` while preserving the planned report contract and service signatures.
- **Files modified:** `app/schemas/reports.py`
- **Verification:** `python -m pytest tests/services/test_report_compare.py tests/services/test_report_builder.py -q`
- **Committed in:** `05ea0b7`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation kept the planned contract executable in the repo’s current Python runtime without changing the required report behavior.

## Issues Encountered
- The first red test run failed on schema import compatibility before it reached the intended `NotImplementedError` assertions; fixing the type-annotation compatibility restored a clean TDD cycle.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase `08-02` can now render strategic reports from a stable typed contract instead of deriving output structure from workflow prose.
- The deterministic builder already exposes the exact buckets, summary, and dropped-ticker metadata that the renderer and workflow integration need next.

---
*Phase: 08-upgrade-outputs-to-strategic-insight-reports*
*Completed: 2026-03-31*
