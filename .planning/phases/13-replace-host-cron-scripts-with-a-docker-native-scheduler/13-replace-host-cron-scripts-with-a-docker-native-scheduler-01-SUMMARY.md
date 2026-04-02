---
phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler
plan: 01
subsystem: infra
tags: [docker, compose, supercronic, pytest, scheduling]
requires:
  - phase: 12-system-diagram-and-readme-architecture-capture
    provides: documented runtime boundaries and operator architecture
provides:
  - reconstructed scheduling regression tests
  - app-container scheduler bootstrap scripts
  - base Docker image and compose runtime contract
affects: [phase-13-02, phase-13-03, docs, operations]
tech-stack:
  added: [Dockerfile, Supercronic v0.2.43]
  patterns: [app-managed scheduler process, dry-run backed test harness]
key-files:
  created: [tests/conftest.py, tests/api/test_scheduling.py, tests/integration/test_scheduled_submission_flow.py, tests/ops/test_docker_scheduler.py, .dockerignore, Dockerfile, ops/docker/start-app-runtime.sh, ops/scheduler/crontab, ops/scheduler/start-supercronic.sh, ops/scheduler/trigger-scheduled.sh]
  modified: [docker-compose.yml]
key-decisions:
  - "Reuse the dry-run doubles in tests so reconstructed scheduler coverage matches the live app seams instead of inventing a second harness."
  - "Expose the app-managed scheduler contract in docker-compose.yml during Plan 01 because the new ops contract test needed a visible app/migrate/postgres runtime before Plan 02."
patterns-established:
  - "Container scheduling stays thin and route-based: shell scripts call the existing token-guarded /runs/trigger/scheduled endpoint."
  - "Scheduler process ownership lives in the app container entrypoint while Postgres and migrations remain separate Compose services."
requirements-completed: [TBD-13-01, TBD-13-02]
duration: 5min
completed: 2026-04-02
---

# Phase 13: Replace Host Cron Scripts With A Docker-Native Scheduler Summary

**Rebuilt the scheduler test harness and shipped the base app-container Docker runtime around Supercronic and the existing scheduled-trigger route**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-02T05:47:15Z
- **Completed:** 2026-04-02T05:51:55Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Recreated route, integration, and ops scheduler tests from source with a deterministic SQLite-backed harness.
- Added the base Docker image, app entrypoint, crontab, and scheduler scripts for an app-container-managed runtime.
- Surfaced the new app-managed scheduler contract in `docker-compose.yml` so the red-to-green ops contract could be proven.

## Task Commits

Each task was committed atomically:

1. **Task 1: Recreate the missing scheduler verification test sources without docs drift work** - `b89504b` (test)
2. **Task 2: Add the base app-container scheduler assets around Supercronic** - `34ef90d` (feat)

## Files Created/Modified
- `tests/conftest.py` - shared app/runtime fixture backed by the dry-run doubles
- `tests/api/test_scheduling.py` - route-level duplicate scheduled-trigger assertions
- `tests/integration/test_scheduled_submission_flow.py` - duplicate scheduled-trigger no-resubmit proof
- `tests/ops/test_docker_scheduler.py` - Compose and scheduler asset contract checks
- `.dockerignore` - keeps the Docker build context tight and deterministic
- `Dockerfile` - installs app dependencies, tzdata, curl, gettext-base, and Supercronic
- `ops/docker/start-app-runtime.sh` - starts Supercronic and uvicorn in one app container with signal cleanup
- `ops/scheduler/crontab` - repo-owned ET weekday schedule contract
- `ops/scheduler/start-supercronic.sh` - renders the env-aware crontab and execs Supercronic
- `ops/scheduler/trigger-scheduled.sh` - token-guarded route wrapper with exact stdout result strings
- `docker-compose.yml` - base postgres/migrate/app runtime contract for the app-managed scheduler path

## Decisions Made
- Reused `app.ops.dry_run` doubles inside the new test harness so reconstructed tests exercise the same mail, research, and Alpaca seams already used by the repo.
- Kept scheduler orchestration in repo-owned shell assets and one app image rather than adding a separate scheduler service or scheduler-owned execution path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Seed valid env before importing `app.main` in tests**
- **Found during:** Task 1 (Recreate the missing scheduler verification test sources without docs drift work)
- **Issue:** Importing `app.main` in the new test harness triggered readiness failures from default placeholder env values before the fixtures could inject dry-run settings.
- **Fix:** Delayed the `create_app` import into the fixture and applied dry-run env overrides first.
- **Files modified:** `tests/conftest.py`
- **Verification:** `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q`
- **Committed in:** `b89504b`

**2. [Rule 3 - Blocking] Expose the app-managed runtime in Compose during Plan 01**
- **Found during:** Task 2 (Add the base app-container scheduler assets around Supercronic)
- **Issue:** The new ops contract test correctly required `postgres`, `migrate`, and `app` in `docker-compose.yml`, so leaving Compose untouched would have kept Task 2 red even with all scheduler assets present.
- **Fix:** Added a minimal three-service Compose runtime early, leaving the broader env and verification tightening for Plan 02.
- **Files modified:** `docker-compose.yml`
- **Verification:** `python -m pytest tests/ops/test_docker_scheduler.py -q`
- **Committed in:** `34ef90d`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both deviations were necessary to make the new scheduler contract executable and verifiable. Scope stayed inside Phase 13.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The app-managed scheduler runtime assets and base Compose contract are in place for Plan 02.
- Compose/env defaults and full route/integration verification still need tightening before the Docker-native operator path is complete.

---
*Phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler*
*Completed: 2026-04-02*
