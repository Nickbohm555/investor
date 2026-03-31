---
phase: 07-build-a-loop-based-quiver-agent
plan: 02
subsystem: api
tags: [research, workflow, runtime, approvals, quiver, testing]
requires:
  - phase: 07-build-a-loop-based-quiver-agent
    provides: typed loop-agent contracts and tool-capable research adapter
provides:
  - bounded Quiver loop execution over ticker-scoped follow-ups
  - trace-aware research node and paused workflow metadata
  - persisted trace visibility through routes and runtime resume seams
affects: [approval-flow, dry-run, readiness, research-pipeline]
tech-stack:
  added: []
  patterns:
    - trace-aware research execution returns explicit execution metadata before deterministic ranking
    - paused workflow state persists research trace fields alongside finalized outcomes and recommendations
key-files:
  created:
    - app/agents/quiver_loop.py
    - tests/agents/test_quiver_loop.py
    - tests/integration/test_loop_research_resume.py
  modified:
    - app/agents/research.py
    - app/graph/workflow.py
    - tests/graph/test_research_node.py
    - tests/graph/test_workflow.py
    - tests/api/test_routes.py
key-decisions:
  - "ResearchNode now exposes `run_with_trace()` and falls back to the legacy JSON-only invoke path only when a tool-capable LLM is unavailable."
  - "Workflow state persists structured trace metadata before approval so downstream handoff logic keeps consuming the same finalized recommendation contract."
patterns-established:
  - "Loop-agent execution returns `ResearchExecutionResult`, then deterministic ranking runs on `execution.outcome`."
  - "Approval and broker handoff remain recommendation-driven while trace metadata rides alongside state payload for auditability."
requirements-completed: [AGENT-01, AGENT-02, AGENT-03]
duration: 8min
completed: 2026-03-31
---

# Phase 07: Build A Loop-Based Quiver Agent Summary

**The repo now runs bounded multi-step Quiver investigation loops, persists why follow-up lookups happened, and keeps the downstream approval and broker-prestage contract unchanged.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-31T20:42:25Z
- **Completed:** 2026-03-31T20:50:40Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `QuiverLoopAgent`, which limits seed tickers, executes one ticker-scoped Quiver lookup per assistant turn, and returns explicit stop reasons plus investigation traces.
- Upgraded `ResearchNode` and workflow execution to use `ResearchExecutionResult` so trace metadata is persisted before deterministic ranking and review pause.
- Extended workflow, route, and runtime integration coverage to prove the paused state carries `research_trace`, `research_stop_reason`, `research_tool_call_count`, and `investigated_tickers` through approval resume.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the bounded Quiver loop with deterministic seed-and-follow-up behavior** - `967db90` (`feat`)
2. **Task 2: Wire trace-aware loop execution into ResearchNode, workflow state, and persisted trigger payloads** - `80ac093` (`feat`)

## Files Created/Modified

- `app/agents/quiver_loop.py` - app-owned serial loop executor over existing ticker-scoped Quiver methods
- `app/agents/research.py` - trace-aware research entrypoint with loop-agent and legacy JSON-only fallback paths
- `app/graph/workflow.py` - paused-state persistence for trace metadata alongside finalized outcomes and recommendations
- `tests/agents/test_quiver_loop.py` - bounded loop coverage for seed selection, ticker-scoped follow-ups, and stop reasons
- `tests/graph/test_research_node.py` - `run_with_trace()` and backward-compatible `run()` coverage
- `tests/graph/test_workflow.py` - workflow-state persistence coverage for trace metadata
- `tests/api/test_routes.py` - route-level persistence assertions for loop metadata through trigger and approval flows
- `tests/integration/test_loop_research_resume.py` - runtime seam coverage proving start/resume retains trace metadata

## Decisions Made

- Keep the loop agent responsible only for investigation and raw `ResearchOutcome` generation; deterministic ranking still runs afterward in Python.
- Persist trace metadata in the same paused workflow state payload already used for approval/review continuity instead of inventing a second storage surface.
- Preserve a compatibility fallback in `ResearchNode` for invoke-only doubles so current tests and deterministic local seams remain usable while the live app moves onto the loop path.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- Phase 7 now has live loop execution and persisted trace metadata, so 07-03 can focus on operator-facing budgets, readiness gating, and dry-run proof.
- The remaining operational gap is surfacing loop settings through app configuration and validating provider capability at startup.

---
*Phase: 07-build-a-loop-based-quiver-agent*
*Completed: 2026-03-31*
