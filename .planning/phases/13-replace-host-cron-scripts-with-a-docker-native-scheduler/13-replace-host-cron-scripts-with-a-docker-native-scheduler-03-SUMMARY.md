---
phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler
plan: 03
subsystem: docs
tags: [readme, operations, docker, alembic, scheduling]
requires:
  - phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler
    provides: compose runtime, env defaults, and scheduler contract tests
provides:
  - docker-native operator README
  - removal of host cron helper scripts
  - migration bootstrap for the container runtime
affects: [phase-14, operations, deployment]
tech-stack:
  added: [alembic.ini]
  patterns: [docker-first operator contract, container migration bootstrap]
key-files:
  created: [tests/ops/test_operational_docs.py, alembic.ini, ops/docker/run-migrations.sh]
  modified: [README.md, Dockerfile, docker-compose.yml, app/db/migrations/env.py]
key-decisions:
  - "Delete the host cron scripts instead of wrapping Docker commands so the repo exposes only one scheduler path."
  - "Bootstrap migrations inside the container runtime by widening Alembic's version table and normalizing the Postgres driver path, preserving the existing migration history."
patterns-established:
  - "Operator docs now center on docker compose up/logs/down for scheduler observability."
  - "Containerized migrations must honor the same psycopg URL normalization as the app runtime."
requirements-completed: [TBD-13-03]
duration: 8min
completed: 2026-04-02
---

# Phase 13: Replace Host Cron Scripts With A Docker-Native Scheduler Summary

**Replaced the host-cron operator workflow with Docker-native docs and removed the old cron scripts while fixing container migration startup**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-02T05:56:30Z
- **Completed:** 2026-04-02T06:03:32Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added docs drift tests that force the README onto the Docker-native scheduler workflow.
- Rewrote the README to use `docker compose up -d --build`, `docker compose logs -f migrate app`, and `docker compose down -v` as the operator contract.
- Deleted the old host cron helper scripts and fixed container migrations so the stack now reaches app startup.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing docs assertions for the app-managed Docker scheduler contract** - `428d9e6` (test)
2. **Task 2: Replace the README cron workflow with Docker commands and remove the host cron scripts** - `2e93c1e` (feat)

## Files Created/Modified
- `tests/ops/test_operational_docs.py` - docs drift coverage for the Docker-native scheduler contract
- `README.md` - Docker-first setup, log inspection, teardown, and checklist guidance
- `alembic.ini` - migration config required by the containerized `alembic upgrade head` path
- `ops/docker/run-migrations.sh` - preps Alembic's version table and runs migrations in the container
- `app/db/migrations/env.py` - normalizes `postgresql://` to `postgresql+psycopg://` for Alembic
- `Dockerfile` - includes `alembic.ini` in the image
- `docker-compose.yml` - drops host Postgres port publishing and routes `migrate` through the repo migration wrapper
- `scripts/cron-install.sh` - removed
- `scripts/cron-status.sh` - removed
- `scripts/cron-trigger.sh` - removed
- `scripts/cron-remove.sh` - removed

## Decisions Made
- Kept the README honest to the shipped runtime by removing the old cron operations section entirely instead of preserving compatibility wrappers.
- Fixed migration startup at the container boundary instead of rewriting historical migration IDs or asking operators to run extra bootstrap steps.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Remove host Postgres port publishing from Compose**
- **Found during:** Task 2 (Replace the README cron workflow with Docker commands and remove the host cron scripts)
- **Issue:** The smoke path failed immediately because `5432` was already allocated by an unrelated local container, and the app stack does not require a host Postgres bind.
- **Fix:** Removed the `5432:5432` publish from `postgres` so the Docker-native stack uses the internal Compose network only.
- **Files modified:** `docker-compose.yml`
- **Verification:** `docker compose up -d --build` advanced past Postgres startup on the next run.
- **Committed in:** `2e93c1e`

**2. [Rule 3 - Blocking] Add Alembic config and migration bootstrap for container startup**
- **Found during:** Task 2 (Replace the README cron workflow with Docker commands and remove the host cron scripts)
- **Issue:** The migrate service initially failed because the image lacked `alembic.ini`, Alembic used the wrong Postgres driver, and the revision IDs exceeded the default `alembic_version.version_num` width.
- **Fix:** Added `alembic.ini`, normalized the Alembic Postgres URL to `psycopg`, and wrapped migrations in `ops/docker/run-migrations.sh` to widen the version table before `alembic upgrade head`.
- **Files modified:** `Dockerfile`, `alembic.ini`, `app/db/migrations/env.py`, `docker-compose.yml`, `ops/docker/run-migrations.sh`
- **Verification:** `docker compose up -d --build` advanced through `postgres` and `migrate`, then reached app startup.
- **Committed in:** `2e93c1e`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were necessary for the documented Docker operator path to work on the shipped stack. No extra product scope was added.

## Issues Encountered
- Final smoke verification could not complete end to end on this machine because host port `8000` is already occupied by the unrelated `web-agent-backend-1` container. The repo-side stack progressed through successful migration startup before hitting that external bind conflict.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 13 implementation is complete and the repo now exposes a single Docker-native scheduler path.
- A clean host with port `8000` available should be used for the final manual operator smoke if needed before broader deployment.

---
*Phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler*
*Completed: 2026-04-02*
