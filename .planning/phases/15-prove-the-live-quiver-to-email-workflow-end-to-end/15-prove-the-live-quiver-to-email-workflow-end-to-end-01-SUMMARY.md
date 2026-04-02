---
phase: 15-prove-the-live-quiver-to-email-workflow-end-to-end
plan: 01
subsystem: operations
tags: [live-proof, quiver, smtp, scheduling, persistence]
requires:
  - phase: 15-prove-the-live-quiver-to-email-workflow-end-to-end
    provides: live-proof CLI contract and persisted run inspection seam
provides:
  - repo-owned live-proof CLI
  - route-backed scheduled trigger helper
  - persisted run inspection helper
affects: [phase-15, operations, live-proof]
tech-stack:
  added: []
  patterns: [repo-owned operator CLI, route-backed trigger seam, persisted-state inspection]
key-files:
  created: [app/ops/live_proof.py, tests/ops/test_live_proof.py]
  modified: []
key-decisions:
  - "Keep the live proof on one repo-owned CLI surface instead of ad hoc shell commands."
  - "Trigger the live run through the shipped scheduled route and inspect proof state from persisted database records."
patterns-established:
  - "Preflight checks now cover Quiver endpoint reachability, one OpenAI-compatible tool-call probe, SMTP login readiness, and approval-boundary reachability."
  - "Operators can inspect persisted run status and related approval or broker counts without raw SQL."
requirements-completed: []
duration: 21min
completed: 2026-04-02
---

# Phase 15: Prove The Live Quiver-To-Email Workflow End To End Summary

**Added the repo-owned live-proof CLI used to preflight external dependencies, trigger the scheduled route, and inspect persisted run state**

## Performance

- **Duration:** 21 min
- **Completed:** 2026-04-02
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added red-first tests that pin the live-proof contract for preflight, scheduled triggering, and persisted run inspection.
- Implemented `python -m app.ops.live_proof` with `preflight`, `trigger-scheduled`, and `inspect-run` subcommands.
- Kept the helper aligned with shipped seams: Quiver client methods, OpenAI-compatible `/chat/completions`, SMTP login rules, the scheduled trigger route header, and persisted DB counts.

## Task Commits

1. **Task 1: Create failing ops coverage for the live-proof helper contract** - `790254b` (test)
2. **Task 2: Implement the repo-owned live-proof CLI against the existing runtime seams** - `64ec4da` (feat)

## Files Created/Modified

- `app/ops/live_proof.py` - argparse CLI for dependency preflight, route-backed scheduled triggering, and persisted run inspection
- `tests/ops/test_live_proof.py` - regression coverage for the live-proof helper contract

## Decisions Made

- Treated any app-originated HTTP response from `<external_base_url>/approval/probe` as reachability success so the preflight checks the approval boundary instead of requiring a special probe route.
- Kept `inspect-run` focused on persisted summary fields and related record counts so operators can verify the live run without raw SQL.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None for this plan. The later live proof still requires real Quiver, LLM, SMTP, and public callback credentials.

## Next Phase Readiness

- Phase 15-01 is complete and the repo now has the CLI surface required by the runbook and live proof.
- Phase 15-02 can now document the exact operator workflow against this command set.

---
*Phase: 15-prove-the-live-quiver-to-email-workflow-end-to-end*
*Completed: 2026-04-02*
