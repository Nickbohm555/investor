---
phase: 03-scheduling-and-email-delivery
plan: 01
subsystem: infra
tags: [cron, scheduling, fastapi, sqlite, operations]
requires:
  - phase: 02
    provides: branch-aware workflow output and persisted run state ready for scheduled execution
provides:
  - schedule-key backed duplicate-safe scheduled trigger route
  - repo-managed cron install, status, remove, and trigger scripts
  - shared SQLite scheduling test harness for duplicate-run coverage
affects: [api, email, operations, testing]
tech-stack:
  added: []
  patterns: [database-backed schedule idempotency, thin repo-managed cron wrappers]
key-files:
  created: [app/services/scheduling.py, app/db/migrations/versions/0002_add_schedule_fields.py, scripts/cron-install.sh, scripts/cron-remove.sh, scripts/cron-status.sh, scripts/cron-trigger.sh, tests/api/test_scheduling.py, tests/ops/test_cron_scripts.py]
  modified: [app/config.py, app/main.py, app/db/models.py, app/api/routes.py, tests/conftest.py]
key-decisions:
  - "Keep duplicate scheduled-run protection in the application/database path, with cron limited to triggering and logging."
  - "Use the shared StaticPool SQLite harness in tests so duplicate scheduled requests exercise the same unique-constraint path as app code."
patterns-established:
  - "Scheduled execution creates a persisted run row first via schedule-key uniqueness, then reuses the normal workflow invoke/persist path only on the new-run branch."
  - "Repo cron scripts manage a named crontab block and defer all idempotency decisions to the app instead of shell locking."
requirements-completed: [SCHD-01, SCHD-02, SCHD-03]
duration: 13min
completed: 2026-03-31
---

# Phase 03: Scheduling And Email Delivery Summary

**Schedule-key backed scheduled triggering with repo-managed cron scripts and duplicate-safe run creation for daily execution**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-31T13:47:00Z
- **Completed:** 2026-03-31T14:02:17Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Added env-backed scheduling settings, persisted `schedule_key` fields, and a dedicated `/runs/trigger/scheduled` route with duplicate detection.
- Created repo-owned cron install, remove, status, and trigger scripts that manage one named crontab block and write observable trigger logs.
- Added SQLite-backed scheduling tests and isolated shell-script tests so duplicate run protection and cron behavior are both verified locally.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add schedule-window persistence and the scheduled trigger endpoint** - `8347d12` (feat)
2. **Task 2: Create repo-managed cron scripts for install, remove, status, and trigger** - `5ff11cb` (feat)

## Files Created/Modified
- `app/services/scheduling.py` - Builds New York market-day schedule keys and performs duplicate-safe scheduled run creation.
- `app/api/routes.py` - Adds the scheduled trigger endpoint and only enters the workflow path for new scheduled runs.
- `app/db/models.py` - Extends persisted runs with schedule metadata and uniqueness.
- `app/db/migrations/versions/0002_add_schedule_fields.py` - Adds schedule columns and the unique schedule-key constraint.
- `scripts/cron-install.sh` - Installs the repo-managed cron block.
- `scripts/cron-remove.sh` - Removes only the managed cron block.
- `scripts/cron-status.sh` - Reports managed-block presence and the cron log path.
- `scripts/cron-trigger.sh` - Loads `.env`, posts to the scheduled trigger route, and appends success or failure log lines.
- `tests/api/test_scheduling.py` - Covers valid, duplicate, and unauthorized scheduled trigger behavior.
- `tests/ops/test_cron_scripts.py` - Verifies install/remove/status/trigger script behavior against fake `crontab` and `curl` seams.

## Decisions Made
- Keep scheduled-run dedupe in the app/database layer so manual retries and future execution paths stay protected without relying on shell locking.
- Reuse the shared in-memory SQLite `StaticPool` harness for scheduling tests so duplicate requests hit the same persisted unique-constraint seam in one app instance.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched scheduled route annotations to Python 3.9-safe typing**
- **Found during:** Task 1 (Add schedule-window persistence and the scheduled trigger endpoint)
- **Issue:** FastAPI could not evaluate `|` union annotations while importing the new scheduled route on this Python 3.9 runtime.
- **Fix:** Replaced the affected route annotations with `Optional[...]` and a broader response mapping annotation.
- **Files modified:** `app/api/routes.py`
- **Verification:** `pytest tests/api/test_scheduling.py -q`
- **Committed in:** `8347d12`

**2. [Rule 3 - Blocking] Added an explicit curl override seam for cron-script tests**
- **Found during:** Task 2 (Create repo-managed cron scripts for install, remove, status, and trigger)
- **Issue:** The required fixed runtime `PATH` in `cron-trigger.sh` bypassed the fake `curl` binary used by the isolated ops tests.
- **Fix:** Added `INVESTOR_CURL_BIN` as an optional override while preserving the stable production `PATH`.
- **Files modified:** `scripts/cron-trigger.sh`, `tests/ops/test_cron_scripts.py`
- **Verification:** `pytest tests/ops/test_cron_scripts.py -q`
- **Committed in:** `5ff11cb`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were execution blockers for this runtime and test harness. They preserved the planned behavior without widening scope.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 now has the scheduled trigger entrypoint and portable cron scripts needed for real delivery work.
- Plan `03-02` can build the SMTP provider and signed public-link memo path on top of this duplicate-safe scheduled foundation.

---
*Phase: 03-scheduling-and-email-delivery*
*Completed: 2026-03-31*
