---
phase: 14-deepen-watchlist-explanations-and-follow-up-guidance
plan: 02
subsystem: reporting
tags: [prompts, reports, testing]
requires:
  - phase: 14-01
    provides: enriched watchlist and research-queue schema contracts
provides:
  - exact watchlist guidance keys in research prompts
  - prompt-preserving watchlist builder mapping
  - exact no-action follow-up defaults
affects: [workflow, email, testing]
tech-stack:
  added: []
  patterns: [shared prompt contract, prompt-first watchlist guidance]
key-files:
  created: [tests/services/test_research_prompt.py]
  modified: [app/services/research_prompt.py, app/services/report_builder.py, tests/services/test_report_builder.py]
key-decisions:
  - "Keep the legacy and final prompt paths on one shared system prompt so watchlist guidance requirements cannot drift between code paths."
  - "Once prompt-supplied watchlist guidance exists, the builder should fall back to summary-derived defaults only when those structured fields are absent."
patterns-established:
  - "Prompt contract changes land with exact-string regression tests so output-schema drift fails fast."
  - "Watchlist builder tests cover both compatibility fallbacks and prompt-populated structured guidance values."
requirements-completed: [WLG-02]
duration: 4min
completed: 2026-04-02
---

# Phase 14 Plan 02: Deepen Watchlist Explanations And Follow-Up Guidance Summary

**Shared research prompts now require explicit watchlist guidance keys, and the deterministic builder preserves prompt-supplied guidance values into the research queue**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-02T06:09:00Z
- **Completed:** 2026-04-02T06:12:59Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added prompt-contract tests that pin the exact watchlist guidance sentence on both final and legacy prompt paths.
- Updated the shared research prompt so watchlist outputs must return `watchlist_reason`, `missing_evidence`, `unresolved_questions`, and `next_steps`.
- Tightened the report builder to preserve prompt-supplied watchlist guidance verbatim and use the exact planned fallback strings for watchlist and no-action outcomes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Recreate prompt-contract tests that require explicit watchlist guidance keys** - `59806b7` (test)
2. **Task 2: Enrich the prompt contract and builder semantics for explicit watchlist guidance** - `84e6861` (feat)

**Plan metadata:** `docs(14-02): complete prompt-guidance enrichment plan`

## Files Created/Modified
- `tests/services/test_research_prompt.py` - Pins the exact watchlist sentence and JSON-only shared prompt contract.
- `tests/services/test_report_builder.py` - Verifies prompt-supplied watchlist guidance is preserved and exact no-action defaults remain stable.
- `app/services/research_prompt.py` - Defines the exact shared system prompt contract for watchlist guidance keys.
- `app/services/report_builder.py` - Prefers prompt-populated watchlist fields and updates exact fallback strings.

## Decisions Made
- Share one system prompt between `build_final_research_payload(...)` and `build_research_prompt_payload(...)` so watchlist contract changes cannot drift across prompt paths.
- Narrow the watchlist fallback mapping once prompt-supplied fields exist, using `outcome.summary` rather than `risk_notes` for missing-evidence fallback when the prompt omits structured values.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated the earlier watchlist fallback regression to the new Phase 14-02 builder contract**
- **Found during:** Task 2 (Enrich the prompt contract and builder semantics for explicit watchlist guidance)
- **Issue:** The `14-01` builder regression still expected the older compatibility fallback of `risk_notes` plus the older "Review..." next-step text, which conflicted with the exact `14-02` contract.
- **Fix:** Updated the earlier test to expect the new `outcome.summary` fallback and the exact "Check the next Quiver refresh before approval." string.
- **Files modified:** `tests/services/test_report_builder.py`
- **Verification:** `python -m pytest tests/services/test_research_prompt.py tests/services/test_report_builder.py -q`
- **Committed in:** `84e6861`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The deviation brought the pre-existing regression coverage forward to the new prompt-enriched builder contract without expanding scope.

## Issues Encountered
- The first green run surfaced an outdated fallback expectation from `14-01`; once aligned to the new plan contract, the prompt and builder tests passed cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan `14-03` can render these named research-queue fields in both text and HTML output without inventing any new data derivation.
- Workflow persistence and README coverage can now verify the same named watchlist keys that the prompt and builder already enforce.

---
*Phase: 14-deepen-watchlist-explanations-and-follow-up-guidance*
*Completed: 2026-04-02*
