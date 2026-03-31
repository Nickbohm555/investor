---
phase: 07-build-a-loop-based-quiver-agent
plan: 01
subsystem: api
tags: [research, prompt, llm, tool-calling, quiver, testing]
requires:
  - phase: 06-replace-langgraph-with-a-custom-workflow-engine
    provides: app-owned workflow/runtime seams without LangGraph coupling
provides:
  - typed bounded-loop research agent contracts
  - trace serialization helpers for persisted workflow state
  - provider-portable tool-capable research adapter coverage
affects: [phase-07-runtime, workflow-state, readiness, dry-run]
tech-stack:
  added: []
  patterns:
    - app-owned typed loop decision contracts
    - raw OpenAI-compatible chat completions for both JSON-only and tool turns
key-files:
  created:
    - app/schemas/research_agent.py
    - app/services/research_trace.py
    - tests/services/test_research_trace.py
  modified:
    - app/services/research_prompt.py
    - app/services/research_llm.py
    - tests/conftest.py
    - tests/services/test_research_prompt.py
    - tests/services/test_research_llm.py
key-decisions:
  - "Phase 7 loop control is expressed through app-owned Pydantic contracts instead of provider-specific response dicts."
  - "The existing HTTP adapter remains the only provider seam; tool support is added by posting raw `/chat/completions` JSON instead of adopting an SDK."
patterns-established:
  - "Prompt builders now separate loop instructions, seed brief construction, and final synthesis payload generation."
  - "Research trace persistence uses a stable serialized step shape before workflow integration begins."
requirements-completed: [AGENT-01]
duration: 4min
completed: 2026-03-31
---

# Phase 07: Build A Loop-Based Quiver Agent Summary

**Phase 7 now has typed loop-agent contracts, bounded-loop prompt builders, trace serialization, and a provider-portable tool-calling seam ready for runtime integration.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T20:38:01Z
- **Completed:** 2026-03-31T20:42:25Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added bounded research agent schemas covering budgets, tool decisions, final decisions, stop decisions, trace steps, and execution results.
- Split the prompt surface into loop-system, seed-brief, and final-synthesis builders while keeping the original `build_research_prompt_payload()` entrypoint compatible.
- Extended the existing HTTP research adapter to support serial tool-calling turns and added shared provider-capability doubles for supported and unsupported flows.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define loop-agent schemas and prompt builders against the existing ResearchOutcome contract** - `09093b1` (`feat`)
2. **Task 2: Extend the existing HTTP research adapter for serial tool-calling turns** - `0f5d167` (`feat`)

## Files Created/Modified

- `app/schemas/research_agent.py` - typed budget, decision, trace, and execution result contracts for the loop agent
- `app/services/research_trace.py` - stable serialization helper for persisted trace metadata
- `app/services/research_prompt.py` - loop-system, seed-brief, final-synthesis, and compatibility prompt builders
- `app/services/research_llm.py` - raw OpenAI-compatible serial tool-calling method on the existing HTTP adapter
- `tests/conftest.py` - shared doubles for supported tool responses, structured finals, and unsupported-provider failures
- `tests/services/test_research_prompt.py` - prompt contract coverage for loop instructions, shortlist construction, and final payload shape
- `tests/services/test_research_trace.py` - trace serialization coverage
- `tests/services/test_research_llm.py` - HTTP adapter coverage for JSON-only and tool-enabled chat completion paths

## Decisions Made

- Keep the app-owned `ResearchOutcome` contract as the final synthesis target and treat loop decisions as separate typed contracts.
- Preserve provider portability by extending the existing `HttpResearchLLM` seam instead of adding the OpenAI SDK or a third-party agent framework.
- Keep unsupported tool-calling providers as an explicit surfaced failure mode for later readiness checks rather than silently downgrading behavior inside the adapter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adjusted new schema typing for the repo's Python 3.9 runtime**
- **Found during:** Task 1
- **Issue:** Initial Phase 7 schema annotations used `str | None` and generic builtins that the active Python 3.9 runtime could not evaluate under Pydantic.
- **Fix:** Replaced those annotations with `Optional[...]`, `List[...]`, and `Dict[...]` forms consistent with the repo runtime.
- **Files modified:** `app/schemas/research_agent.py`
- **Verification:** `pytest tests/services/test_research_prompt.py tests/services/test_research_trace.py -q`
- **Committed in:** `09093b1`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required runtime compatibility fix only. No scope creep and no contract changes.

## Issues Encountered

- The first Task 1 green attempt exposed a Python 3.9 typing compatibility issue in the new schema layer. Converting the annotations to the repo runtime style resolved it cleanly.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- The repo now has the typed loop contracts and tool-capable LLM seam required to build the actual bounded Quiver loop in 07-02.
- Readiness and dry-run validation for provider capability remain for 07-03, where tool support will become an operator-facing startup concern.

---
*Phase: 07-build-a-loop-based-quiver-agent*
*Completed: 2026-03-31*
