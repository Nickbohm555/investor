---
phase: 20-direct-post-triggered-research-to-email-run-path
plan: 03
subsystem: documentation
tags: [docs, operations, live-proof, runbook]
requires:
  - phase: 20-direct-post-triggered-research-to-email-run-path
    provides: stable manual proof CLI commands and route contract
provides:
  - phase 20 runbook
  - phase 20 proof artifact template
  - readme routing to the manual proof path
affects: [phase-20, docs, operations]
tech-stack:
  added: []
  patterns: [docs drift enforcement, phase-local proof artifact template, README operator routing]
key-files:
  created: [.planning/phases/20-direct-post-triggered-research-to-email-run-path/20-LIVE-PROOF-RUNBOOK.md, .planning/phases/20-direct-post-triggered-research-to-email-run-path/20-LIVE-PROOF-RESULT.md]
  modified: [README.md, tests/ops/test_operational_docs.py]
key-decisions:
  - "Make Phase 20 the active proof workflow in README instead of the older scheduled Phase 19 route."
  - "Treat delivered email as the proof target and keep approval-host verification as an observation step rather than a click requirement."
patterns-established:
  - "Phase-local docs now pin the exact preflight, trigger-manual, and inspect-run commands for direct POST proof."
  - "The proof result template records both blocker evidence and success evidence for the manual trigger path."
requirements-completed: [PH20-03]
duration: 16min
completed: 2026-04-03
---

# Phase 20: Direct POST-triggered research-to-email run path Summary

**Published the operator-facing direct POST proof workflow, result template, and README routing for the new manual trigger path**

## Performance

- **Duration:** 16 min
- **Completed:** 2026-04-03
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added docs drift coverage for the active Phase 20 manual proof workflow.
- Routed README live-proof guidance to the new Phase 20 runbook and manual trigger command.
- Added a Phase 20 runbook and result template that record preflight blockers, manual trigger metadata, inbox evidence, and approval-host observations.

## Task Commits

1. **Task 1: Add red docs drift tests for the Phase 20 manual proof workflow** - `3be6c55` (test)
2. **Task 2: Publish the Phase 20 runbook, result template, and README routing** - `78c3040` (docs)

## Files Created/Modified

- `tests/ops/test_operational_docs.py` - locks the active README, Phase 20 runbook, and Phase 20 result template contract
- `README.md` - points operators to the direct POST proof path and command set
- `.planning/phases/20-direct-post-triggered-research-to-email-run-path/20-LIVE-PROOF-RUNBOOK.md` - explains preflight, runtime start, direct trigger, inbox proof, approval-host verification, run inspection, and failure markers
- `.planning/phases/20-direct-post-triggered-research-to-email-run-path/20-LIVE-PROOF-RESULT.md` - provides the fill-in artifact template for success or blocker evidence

## Decisions Made

- Moved the active operator docs to the manual POST path because Phase 20 is now the narrowest truthful live proof for the product goal.
- Kept approval-link clicking out of scope while still requiring the rendered host to be recorded from the delivered memo.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The new docs drift tests initially failed because the Phase 20 proof artifacts did not exist yet and README still pointed at the scheduled Phase 19 workflow.

## User Setup Required

None for this plan. Running the live proof still requires valid env values, a reachable runtime, and manual inbox verification.

## Next Phase Readiness

- All three Phase 20 plans are now implemented and documented against one consistent direct POST proof workflow.
- The next verification step can use the Phase 20 runbook and CLI to evaluate real-environment blockers or success evidence.

---
*Phase: 20-direct-post-triggered-research-to-email-run-path*
*Completed: 2026-04-03*
