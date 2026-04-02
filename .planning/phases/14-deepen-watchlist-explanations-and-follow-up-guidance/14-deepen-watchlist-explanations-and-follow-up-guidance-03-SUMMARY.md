---
phase: 14-deepen-watchlist-explanations-and-follow-up-guidance
plan: 03
subsystem: reporting
tags: [reports, templates, workflow, docs, testing]
requires:
  - phase: 14-02
    provides: shared watchlist guidance prompt contract and builder semantics
provides:
  - shared research-queue rendering labels
  - persisted workflow coverage for named watchlist guidance fields
  - README documentation of the richer watchlist and no-action memo surface
affects: [workflow, email, docs, testing]
tech-stack:
  added: []
  patterns: [shared research-queue rendering, persisted report payload verification]
key-files:
  created: []
  modified: [README.md, app/templates/reports/strategic_report.txt.j2, app/templates/reports/strategic_report.html.j2, tests/graph/test_workflow_reporting.py]
key-decisions:
  - "Keep watchlist and no-action guidance inside one shared `Research Queue` section with neutral labels instead of branching to separate output formats."
  - "Verify the persisted workflow payload through the existing `report.model_dump(mode=\"python\")` path rather than adding duplicate persistence-specific code."
patterns-established:
  - "Rendered report sections use the same named research-queue fields that persist in workflow state."
  - "README wording for operator-visible report changes is locked by an exact drift assertion."
requirements-completed: [WLG-03]
duration: 5min
completed: 2026-04-02
---

# Phase 14 Plan 03: Deepen Watchlist Explanations And Follow-Up Guidance Summary

**Text and HTML reports now render shared why-not-now guidance labels, workflow state persists the same named research-queue fields, and the README documents the richer watchlist/no-action memo surface**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-02T06:13:00Z
- **Completed:** 2026-04-02T06:17:41Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Recreated rendering, workflow-persistence, and README drift coverage for the enriched shared research-queue surface.
- Updated the text and HTML strategic report templates to render neutral labels for why an idea is not actionable, what evidence is missing, which questions remain, and what to check next.
- Added the exact README dry-run sentence describing the shared watchlist/no-action memo surface and verified workflow persistence through the existing report payload path.

## Task Commits

Each task was committed atomically:

1. **Task 1: Recreate rendering, workflow-persistence, and README drift tests for the richer shared research-queue report** - `12578cc` (test)
2. **Task 2: Render the richer shared research-queue sections, prove persistence, and document the new operator-visible memo shape** - `af78b29` (feat)

**Plan metadata:** `docs(14-03): complete report-surface rendering plan`

## Files Created/Modified
- `tests/services/test_report_render.py` - Pins the shared research-queue labels in rendered text and HTML output.
- `tests/graph/test_workflow_reporting.py` - Verifies persisted `strategic_report["research_queue"][0]` includes the named guidance keys for both watchlist and no-action runs.
- `tests/ops/test_operational_docs.py` - Locks the README dry-run wording for the richer shared memo surface.
- `app/templates/reports/strategic_report.txt.j2` - Renders the named guidance fields in the shared text report.
- `app/templates/reports/strategic_report.html.j2` - Renders the same labels and empty-state fallbacks in the HTML report.
- `README.md` - Documents the richer shared watchlist/no-action memo surface in the dry-run section.

## Decisions Made
- Preserve a single `Research Queue` report format for both watchlist and no-action outcomes so operators learn one stable memo surface.
- Trust the existing workflow persistence seam of `report.model_dump(mode="python")` and prove it in tests instead of adding redundant persistence logic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated the workflow test harness to match the compiled workflow's quiver-client and evidence-builder interfaces**
- **Found during:** Task 2 (Render the richer shared research-queue sections, prove persistence, and document the new operator-visible memo shape)
- **Issue:** The first workflow persistence test used placeholder stubs that did not satisfy the real `CompiledInvestorWorkflow._build_evidence_bundles(...)` interface, so the test failed before it reached the persistence assertions.
- **Fix:** Replaced the placeholder object with a quiver-client stub exposing the four expected methods and widened the test evidence-builder stub to accept the real keyword arguments.
- **Files modified:** `tests/graph/test_workflow_reporting.py`
- **Verification:** `python -m pytest tests/services/test_report_render.py tests/graph/test_workflow_reporting.py tests/ops/test_operational_docs.py -q`
- **Committed in:** `af78b29`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation aligned the recreated workflow test with the real runtime seam without changing application behavior or plan scope.

## Issues Encountered
- The first red workflow test failed on stub shape mismatches before it reached the persistence assertion; fixing the harness exposed the intended behavior and kept the application code unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 14 is complete: the watchlist/no-action contract is now enriched upstream, persisted structurally, rendered visibly, and documented for operators.
- Future phases can consume the same named `research_queue` fields in any UI or audit tooling without reverse-engineering email text.

---
*Phase: 14-deepen-watchlist-explanations-and-follow-up-guidance*
*Completed: 2026-04-02*
