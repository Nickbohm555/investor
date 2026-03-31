---
phase: 02-quiver-research-and-ranking
plan: 02
subsystem: research
tags: [prompting, pydantic, research, llm]
requires:
  - phase: 02
    provides: canonical ticker evidence bundles from Quiver normalization
provides:
  - discriminated research outcome schemas
  - evidence-aware prompt payload generation
affects: [workflow, ranking, email]
tech-stack:
  added: []
  patterns: [discriminated research outcomes, injected prompt builders]
key-files:
  created: [app/schemas/research.py, app/services/research_prompt.py, tests/services/test_research_prompt.py]
  modified: [app/agents/research.py, app/schemas/workflow.py, tests/graph/test_research_node.py]
key-decisions:
  - "Make candidate, watchlist, and no-action outcomes explicit discriminated branches."
  - "Inject prompt building into ResearchNode so workflow code can pass normalized evidence and tests can assert payload shape."
patterns-established:
  - "ResearchNode validates JSON with TypeAdapter over the ResearchOutcome union."
  - "Prompt assembly consumes canonical TickerEvidenceBundle input instead of raw Quiver rows."
requirements-completed: [RSCH-02]
duration: 4min
completed: 2026-03-31
---

# Phase 02: Quiver Research And Ranking Summary

**Discriminated research outcomes and evidence-driven prompt payloads that force candidate, watchlist, or no-action branches through validated JSON**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T05:54:31Z
- **Completed:** 2026-03-31T05:58:26Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added explicit candidate, watchlist, and no-action research outcome schemas with evidence fields.
- Converted the research node to validate `ResearchOutcome` JSON via `TypeAdapter`.
- Built prompt payload assembly from canonical evidence bundles and covered prompt content plus invalid-shape rejection in tests.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define discriminated research outcome schemas with explicit evidence fields** - `4bbeca3` (feat)
2. **Task 2: Build the research prompt payload and parse structured outcomes in the research node** - `a0e8e0f` (feat)

## Files Created/Modified
- `app/schemas/research.py` - Discriminated research outcome and recommendation schemas.
- `app/schemas/workflow.py` - Workflow-facing exports that surface the new research contracts.
- `app/agents/research.py` - Prompt-builder injection and JSON validation against `ResearchOutcome`.
- `app/services/research_prompt.py` - Prompt payload construction from normalized ticker evidence bundles.
- `tests/graph/test_research_node.py` - Outcome-branch parsing and invalid-shape validation tests.
- `tests/services/test_research_prompt.py` - Prompt content tests for required outcomes and evidence fields.

## Decisions Made
- Represent the research result as a discriminated union so downstream code can branch explicitly on candidates, watchlist, and no-action outcomes.
- Make prompt construction injectable at the node boundary so tests can assert payload wiring without mocking internals.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched discriminated union syntax to Python 3.9-compatible `Union[...]`**
- **Found during:** Task 1 (Define discriminated research outcome schemas with explicit evidence fields)
- **Issue:** The repo runtime raised a `TypeError` when evaluating `CandidateOutcome | WatchlistOutcome | NoActionOutcome`.
- **Fix:** Replaced the shorthand with `Union[...]` inside the discriminated `ResearchOutcome` declaration.
- **Files modified:** app/schemas/research.py
- **Verification:** `pytest tests/graph/test_research_node.py -q`
- **Committed in:** `4bbeca3`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix preserved the intended schema design without changing behavior or scope.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Workflow code can now receive normalized evidence bundles and return a validated structured research branch.
- Ranking, branch-aware email rendering, and trigger/workflow wiring remain for `02-03`.

---
*Phase: 02-quiver-research-and-ranking*
*Completed: 2026-03-31*
