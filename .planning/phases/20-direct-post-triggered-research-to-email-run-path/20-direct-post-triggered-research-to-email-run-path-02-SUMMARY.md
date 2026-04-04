---
phase: 20-direct-post-triggered-research-to-email-run-path
plan: 02
subsystem: operations
tags: [live-proof, manual-trigger, operations, testing]
requires:
  - phase: 20-direct-post-triggered-research-to-email-run-path
    provides: stable manual POST route contract
provides:
  - staged readiness-first preflight
  - trigger-manual CLI command
  - manual proof helper coverage
affects: [phase-20, operations, config]
tech-stack:
  added: []
  patterns: [readiness-first diagnostics, direct route trigger helper, backward-compatible proof payload]
key-files:
  created: []
  modified: [app/config.py, app/ops/live_proof.py, tests/ops/test_live_proof.py, tests/ops/test_manual_post_proof.py]
key-decisions:
  - "Extend the existing app.ops.live_proof CLI instead of creating a second manual-proof tool."
  - "Treat readiness errors as the first blocking failures and skip Quiver and LLM probes when they already explain why a live run cannot proceed."
patterns-established:
  - "Preflight now preserves the old keys while adding manual_trigger_url and first_blocking_failure for the manual operator path."
  - "trigger-manual posts directly to POST /runs/trigger and returns the route body with HTTP status metadata."
requirements-completed: [PH20-02]
duration: 23min
completed: 2026-04-03
---

# Phase 20: Direct POST-triggered research-to-email run path Summary

**Extended the repo-owned live-proof CLI with staged readiness diagnostics and a direct manual trigger command that preserves route response metadata**

## Performance

- **Duration:** 23 min
- **Completed:** 2026-04-03
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added red-first coverage for the `trigger-manual` CLI command and for readiness-first preflight short-circuit behavior.
- Added `manual_trigger_url` configuration and a `_trigger_manual(...)` helper that returns `status_code`, `ok`, and the decoded route payload.
- Reordered preflight behavior so repo readiness errors become the first blocking failures and prevent unnecessary Quiver or LLM calls while preserving backward-compatible payload keys.

## Task Commits

1. **Task 1: Create red tests for staged manual-post preflight and trigger helper behavior** - `7ae0318` (test)
2. **Task 2: Implement staged preflight ordering and a direct manual trigger command** - `7ce3887` (feat)

## Files Created/Modified

- `app/config.py` - adds `manual_trigger_url` for the direct operator POST path
- `app/ops/live_proof.py` - imports readiness checks, short-circuits on blocking env failures, and adds `trigger-manual`
- `tests/ops/test_live_proof.py` - locks the expanded preflight payload and backward-compatible readiness semantics
- `tests/ops/test_manual_post_proof.py` - covers the new CLI verb and readiness-first short-circuit behavior

## Decisions Made

- Kept approval reachability as warning-only even in the manual proof path, while surfacing repo readiness errors as the first blocking failures.
- Preserved the older preflight keys so existing docs and Phase 19 checks do not need a second contract migration.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Existing live-proof tests used placeholder-like settings values, so the green step had to give them readiness-safe defaults once preflight started enforcing the shared readiness contract.

## User Setup Required

None for this plan. Live use still requires valid env values and a running app at `manual_trigger_url`.

## Next Phase Readiness

- Plan 20-02 is complete and gives operators one repo-owned surface for preflight, manual trigger, and run inspection.
- Plan 20-03 can now document the Phase 20 workflow against stable commands and payload fields instead of draft behavior.

---
*Phase: 20-direct-post-triggered-research-to-email-run-path*
*Completed: 2026-04-03*
