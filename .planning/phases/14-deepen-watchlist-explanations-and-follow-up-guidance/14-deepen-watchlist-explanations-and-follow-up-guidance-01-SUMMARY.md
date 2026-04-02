---
phase: 14-deepen-watchlist-explanations-and-follow-up-guidance
plan: 01
subsystem: reporting
tags: [reports, pydantic, workflow, testing]
requires:
  - phase: 08-01
    provides: typed strategic insight report schema and deterministic report builder seams
provides:
  - explicit watchlist candidate guidance fields
  - enriched research queue report contract
  - compatibility-safe watchlist and no-action builder defaults
affects: [workflow, email, testing]
tech-stack:
  added: []
  patterns: [schema-first report enrichment, shared research-queue contract]
key-files:
  created: [tests/services/test_report_contracts.py, tests/services/test_report_builder.py]
  modified: [app/schemas/research.py, app/schemas/reports.py, app/schemas/workflow.py, app/services/report_builder.py]
key-decisions:
  - "Persist watchlist guidance as explicit named fields on both watchlist candidates and research-queue report items instead of deriving everything from generic uncertainty text."
  - "Keep no-action output on the same `research_queue` contract by supplying deterministic fallback watchlist guidance values rather than creating a second report shape."
patterns-established:
  - "Watchlist explanation depth belongs in typed schemas and deterministic builder mappings before prompt or template enrichment."
  - "Workflow consumers continue importing report contracts through `app.schemas.workflow` while the builder owns compatibility defaults."
requirements-completed: [WLG-01]
duration: 6min
completed: 2026-04-02
---

# Phase 14 Plan 01: Deepen Watchlist Explanations And Follow-Up Guidance Summary

**Explicit watchlist guidance fields on research outcomes and strategic report research-queue entries, with deterministic builder defaults for watchlist and no-action paths**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-02T06:02:30Z
- **Completed:** 2026-04-02T06:08:54Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Recreated the missing report contract and builder tests that pin the richer watchlist guidance surface.
- Added `WatchlistCandidate` plus enriched `ResearchNeededItem` fields so the report contract now names why an idea is not actionable, what evidence is missing, which questions remain, and what to check next.
- Updated the deterministic report builder to populate the shared `research_queue` contract for both watchlist and no-action outcomes without inventing a second report format.

## Task Commits

Each task was committed atomically:

1. **Task 1: Recreate the missing report-contract tests and pin the enriched watchlist schema surface** - `ad4ff00` (test)
2. **Task 2: Implement the enriched watchlist and report contracts with compatibility-safe builder defaults** - `a95e3b3` (feat)

**Plan metadata:** `docs(14-01): complete enriched watchlist contract plan`

## Files Created/Modified
- `tests/services/test_report_contracts.py` - Pins the explicit watchlist candidate and research queue field surface.
- `tests/services/test_report_builder.py` - Verifies deterministic watchlist and no-action `research_queue` output.
- `app/schemas/research.py` - Defines `WatchlistCandidate` and upgrades `WatchlistOutcome.items`.
- `app/schemas/reports.py` - Replaces generic research queue fields with named watchlist guidance fields.
- `app/schemas/workflow.py` - Re-exports `WatchlistCandidate` through the workflow schema surface.
- `app/services/report_builder.py` - Maps watchlist and no-action outcomes into the enriched shared report contract.

## Decisions Made
- Persist richer watchlist explanation data as explicit typed fields so later prompt, rendering, and workflow work can consume durable structured values.
- Preserve one shared `research_queue` output surface across watchlist and no-action branches by using deterministic builder defaults instead of branch-specific report models.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Aligned the recreated schema assertion with the repo's `typing.List[...]` schema annotations**
- **Found during:** Task 2 (Implement the enriched watchlist and report contracts with compatibility-safe builder defaults)
- **Issue:** The recreated test initially asserted against `list[...]`, but the existing schema modules use `typing.List[...]`, causing a false red/green mismatch unrelated to the planned behavior.
- **Fix:** Updated the recreated test to assert `List[WatchlistCandidate]`, matching the plan wording and the repo's schema style.
- **Files modified:** `tests/services/test_report_contracts.py`
- **Verification:** `python -m pytest tests/services/test_report_contracts.py tests/services/test_report_builder.py -q`
- **Committed in:** `a95e3b3`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation kept the recreated regression test aligned with the repo's existing type-annotation style without changing the intended contract.

## Issues Encountered
- The first green run exposed a type-annotation mismatch in the recreated test rather than a schema implementation bug; correcting the assertion restored the intended contract verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan `14-02` can now teach the prompt and builder to populate the new watchlist guidance fields directly.
- The report contract and builder surface are stable for rendering and workflow persistence work in `14-03`.

---
*Phase: 14-deepen-watchlist-explanations-and-follow-up-guidance*
*Completed: 2026-04-02*
