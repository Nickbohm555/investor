---
phase: 03-scheduling-and-email-delivery
plan: 02
subsystem: email
tags: [smtp, email, approvals, fastapi, testing]
requires:
  - phase: 03-01
    provides: duplicate-safe scheduled triggering and cron-managed execution entrypoints
provides:
  - env-backed SMTP provider abstraction
  - structured daily memo rendering for candidates, watchlist, and no-action outcomes
  - signed approval and rejection links built from the configured external base URL
affects: [api, workflow, runtime, operations, testing]
tech-stack:
  added: []
  patterns: [provider-driven mail delivery, config-built approval links, structured memo schemas]
key-files:
  created: [app/services/mail_provider.py]
  modified: [app/config.py, app/main.py, app/api/routes.py, app/schemas/workflow.py, app/services/email.py, app/services/tokens.py, app/graph/runtime.py, app/graph/workflow.py, tests/services/test_mail_provider.py, tests/services/test_email.py, tests/services/test_tokens.py, tests/graph/test_workflow.py, tests/conftest.py]
key-decisions:
  - "Compose approval and rejection URLs inside the workflow from configured settings instead of passing request-derived links through runtime state."
  - "Represent memo output as explicit candidate, watchlist, and no-action content so rendering stays detached from provider transport."
patterns-established:
  - "Mail delivery is always provider-driven through app.state.mail_provider rather than a console-only helper."
  - "Approval links are signed per run and decision, then composed from external_base_url at send time."
requirements-completed: [MAIL-01, MAIL-02, MAIL-03]
duration: 28min
completed: 2026-03-31
---

# Phase 03: Scheduling And Email Delivery Summary

**SMTP-backed daily memo delivery with structured candidate/watchlist/no-action rendering and signed public approval links**

## Performance

- **Duration:** 28 min
- **Started:** 2026-03-31T14:12:05Z
- **Completed:** 2026-03-31T14:40:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Added env-backed SMTP configuration plus a reusable `MailProvider` / `SmtpMailProvider` seam for real delivery.
- Replaced the ticker-list email placeholder with structured candidate, watchlist, and no-action memo rendering.
- Threaded signed approval and rejection links through the workflow using `INVESTOR_EXTERNAL_BASE_URL` and token TTL settings.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the mail provider abstraction and SMTP settings** - `e6e00e3` (feat)
2. **Task 2: Render structured memos and signed approval links from configured public URLs** - `c87d3a4` (feat)

## Files Created/Modified
- `app/services/mail_provider.py` - Defines the provider protocol and stdlib SMTP adapter.
- `app/services/email.py` - Renders text and HTML memos for ranked candidates, watchlist items, and no-action reasons.
- `app/services/tokens.py` - Signs and verifies run-scoped approval tokens with expiry enforced by `itsdangerous`.
- `app/graph/workflow.py` - Builds memo content, composes signed public URLs, and sends through the injected provider.
- `app/graph/runtime.py` - Passes the new workflow seam and quiver client state into the provider-driven workflow.
- `app/api/routes.py` - Compiles the workflow with `settings` and `mail_provider` for both manual and scheduled triggers.
- `tests/services/test_mail_provider.py` - Verifies SMTP message construction, STARTTLS, login, and sender/recipient wiring.
- `tests/services/test_email.py` - Verifies the three memo modes and the explicit approval/rejection link text.
- `tests/services/test_tokens.py` - Verifies token round-tripping and expiry behavior.
- `tests/graph/test_workflow.py` - Verifies provider sends, public-host links, and token payload scoping in workflow execution.

## Decisions Made
- Compose approval URLs inside the workflow from configuration so delivery behavior is stable across manual, scheduled, and future external trigger paths.
- Keep the renderer focused on structured memo content and keep transport concerns in the SMTP provider so future non-SMTP providers can slot in cleanly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated the runtime seam to pass `quiver_client` through workflow state**
- **Found during:** Task 2 (Render structured memos and signed approval links from configured public URLs)
- **Issue:** The plan changed the workflow constructor to `compile_workflow(research_node, settings, mail_provider)`, which no longer had a constructor slot for the per-run `quiver_client`.
- **Fix:** Moved `quiver_client` into invoke-time state and updated runtime/tests to use the new seam.
- **Files modified:** `app/graph/runtime.py`, `app/graph/workflow.py`, `tests/graph/test_workflow.py`
- **Verification:** `pytest tests/services/test_mail_provider.py tests/services/test_email.py tests/services/test_tokens.py tests/graph/test_workflow.py -q`
- **Committed in:** `c87d3a4`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation was required to make the planned workflow signature executable without reintroducing request-host URL composition or console mail paths.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 now has real SMTP delivery, structured memo content, and signed public approval links wired through both trigger paths.
- Plan `03-03` can focus on operational logging, duplicate-send verification, and README/operator validation without revisiting the delivery seam.

---
*Phase: 03-scheduling-and-email-delivery*
*Completed: 2026-03-31*
