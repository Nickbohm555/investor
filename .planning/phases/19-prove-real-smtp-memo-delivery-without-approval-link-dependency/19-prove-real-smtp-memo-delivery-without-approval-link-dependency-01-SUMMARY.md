---
phase: 19-prove-real-smtp-memo-delivery-without-approval-link-dependency
plan: 01
subsystem: operations
tags: [smtp, live-proof, operations, testing]
requires:
  - phase: 15-prove-the-live-quiver-to-email-workflow-end-to-end
    provides: live-proof CLI and SMTP memo delivery seam
provides:
  - split preflight readiness contract
  - shared smtp transport selection
  - smtp transport regression coverage
affects: [phase-19, operations, smtp]
tech-stack:
  added: []
  patterns: [shared smtp transport helper, blocking-vs-warning preflight reporting, transport-mode diagnostics]
key-files:
  created: [tests/services/test_mail_provider.py]
  modified: [app/config.py, app/services/mail_provider.py, app/ops/live_proof.py, tests/ops/test_live_proof.py]
key-decisions:
  - "Keep approval-link reachability as a warning-only preflight signal while SMTP readiness remains the blocking proof gate."
  - "Drive both live-proof preflight and real memo sends through one SMTP transport helper so STARTTLS and implicit TLS cannot drift."
patterns-established:
  - "smtp_security now resolves explicit or auto transport mode and fails fast with Unsupported SMTP transport mode when configuration and port do not agree."
  - "Live proof preflight now reports smtp_ready, approval_reachability_ready, blocking_failures, and warnings in one payload."
requirements-completed: [SMTP-19-02, SMTP-19-04]
duration: 18min
completed: 2026-04-03
---

# Phase 19: Prove Real SMTP Memo Delivery Without Approval-Link Dependency Summary

**Split the live-proof preflight into blocking SMTP readiness and warning-only approval reachability while adding shared STARTTLS or SSL transport handling**

## Performance

- **Duration:** 18 min
- **Completed:** 2026-04-03
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added red-first tests that pin the Phase 19 preflight payload and SMTP transport-mode contract.
- Implemented a shared SMTP transport helper that supports STARTTLS on 587, implicit TLS on 465, and clear unsupported-mode failures.
- Updated `app.ops.live_proof` so SMTP transport errors become blocking diagnostics while unreachable approval hosts remain warnings.

## Task Commits

1. **Task 1: Add failing tests for the split preflight contract and SMTP transport modes** - `a05d228` (test)
2. **Task 2: Implement split preflight status and shared SMTP transport handling** - `ea515db` (feat)

## Files Created/Modified

- `app/config.py` - adds `smtp_security` configuration for explicit or auto transport-mode selection
- `app/services/mail_provider.py` - centralizes SMTP transport resolution, connection setup, and preflight inspection
- `app/ops/live_proof.py` - reports blocking SMTP readiness separately from warning-only approval reachability
- `tests/ops/test_live_proof.py` - locks the new preflight payload shape and unsupported transport diagnostic behavior
- `tests/services/test_mail_provider.py` - covers STARTTLS, implicit TLS, and unsupported configuration handling

## Decisions Made

- Used `"auto"` transport detection only for the standard ports 587 and 465; any other combination now fails fast instead of guessing.
- Preserved the existing scheduled-route proof path and limited the Phase 19 contract change to truthfully classifying proof blockers vs warnings.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- An existing preflight test still asserted the old payload shape; it was updated in the green step to match the new Phase 19 contract.

## User Setup Required

None for this plan. The later live proof still needs working Quiver, LLM, SMTP, and runtime credentials.

## Next Phase Readiness

- Phase 19-01 is complete and the code now exposes the truthful SMTP-vs-approval preflight contract that the Phase 19 runbook can document.
- Phase 19-02 can update README and proof artifacts against the new split-status behavior without changing runtime code again.

---
*Phase: 19-prove-real-smtp-memo-delivery-without-approval-link-dependency*
*Completed: 2026-04-03*
