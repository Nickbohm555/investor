---
phase: 06-replace-langgraph-with-a-custom-workflow-engine
plan: 04
subsystem: infra
tags: [docs, config, dependencies, ops]
requires:
  - phase: 06-replace-langgraph-with-a-custom-workflow-engine
    provides: workflow-engine cutover in app and API code
provides:
  - repo surface without LangGraph dependencies or operator env vars
  - updated operator docs for the app-owned workflow engine
  - final verification proving dry-run, docs, and full test suite on the cutover
affects: [README, env-template, pyproject, dry-run, test-harnesses]
tech-stack:
  added: []
  patterns:
    - repo docs and tests lock the app-owned workflow engine terminology
    - stale LangGraph-era test harness inputs are removed when they no longer reflect runtime behavior
key-files:
  created: []
  modified:
    - pyproject.toml
    - app/config.py
    - app/graph/runtime.py
    - app/graph/workflow.py
    - README.md
    - .env.example
    - tests/ops/test_operational_docs.py
    - tests/services/test_broker_policy.py
    - tests/services/test_persistence.py
    - tests/integration/test_durable_workflow.py
key-decisions:
  - "The repo now describes the system as app-owned end to end, including docs, envs, and residual test scaffolding."
  - "Dead runtime shims were simplified enough to stop referencing LangGraph even if they remain in-tree."
patterns-established:
  - "Cleanup phases should update lingering tests and helpers so full-suite verification reflects the new contract, not just the targeted slice."
requirements-completed: [SC-01, SC-03]
duration: 6min
completed: 2026-03-31
---

# Phase 06 Plan 04 Summary

**The repository surface now reflects one app-owned workflow engine, with LangGraph dependencies, config, docs language, and stale test harness references removed.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-31T20:30:00Z
- **Completed:** 2026-03-31T20:36:07Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Removed LangGraph packages from `pyproject.toml` and deleted the operator-facing env/config setting for a checkpointer URL.
- Rewrote docs and ops-proof tests around the app-owned workflow engine wording and setup path.
- Cleaned up remaining test/runtime shims so the full suite passes without any LangGraph/checkpointer references outside the archival migration marker.

## Task Commits

The dependency, config, docs, and residual harness cleanup landed together as one focused cleanup commit:

1. **Tasks 1-2: Remove LangGraph repo surface and align docs/harnesses** - `2066b50` (`chore`)

## Files Created/Modified

- `pyproject.toml` - LangGraph packages removed
- `app/config.py` - no checkpointer setting remains
- `app/graph/runtime.py` - simplified compatibility shim without LangGraph imports
- `app/graph/workflow.py` - compile signature no longer exposes a checkpointer seam
- `README.md` - app-owned workflow wording
- `.env.example` - no LangGraph env var
- `tests/ops/test_operational_docs.py` - docs/env assertions updated
- `tests/conftest.py` - removed stale checkpointer test harness input
- `tests/integration/test_durable_workflow.py` - restart-safe expectations updated to the persisted-step flow
- `tests/services/test_broker_policy.py` - run fixture updated to the phase-6 run shape

## Decisions Made

- Removed stale LangGraph-era seams from test harnesses and compatibility helpers so the repository no longer tells two different stories about how workflow execution works.
- Kept the phase-6 migration marker string intact because it is part of the archival payload contract for pre-cutover runs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated residual tests outside the explicit plan file list to keep full-suite verification green**
- **Found during:** Final full-suite verification
- **Issue:** Several older tests still created runs with `thread_id` or asserted `resuming`, which no longer matched the phase-6 runtime contract.
- **Fix:** Updated those fixtures and expectations to the app-owned workflow engine shape.
- **Files modified:** `tests/services/test_broker_policy.py`, `tests/integration/test_durable_workflow.py`, `tests/graph/test_workflow.py`, `tests/services/test_persistence.py`
- **Verification:** `python -m pytest -q`
- **Committed in:** `2066b50`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to prove the repo is coherently post-LangGraph, not just the targeted ops slice.

## Issues Encountered

- The full suite exposed a handful of older tests that were still seeding pre-phase6 run shapes. Updating those helpers was straightforward once the final run schema was stable.

## User Setup Required

None.

## Next Phase Readiness

- Phase 7 can build the loop-based Quiver agent on top of a fully app-owned workflow engine.
- The repo now has a clean dependency and operator surface for the post-LangGraph runtime.

---
*Phase: 06-replace-langgraph-with-a-custom-workflow-engine*
*Completed: 2026-03-31*
