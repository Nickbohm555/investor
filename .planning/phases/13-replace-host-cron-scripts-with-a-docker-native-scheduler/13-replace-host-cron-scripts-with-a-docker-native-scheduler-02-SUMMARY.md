---
phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler
plan: 02
subsystem: infra
tags: [docker, compose, supercronic, pytest, env]
requires:
  - phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler
    provides: base Docker scheduler assets and reconstructed scheduling tests
provides:
  - compose-safe env defaults for Docker-native scheduling
  - clean checkout compose rendering
  - dedupe-safe dry-run env wiring
affects: [phase-13-03, operations, docs]
tech-stack:
  added: []
  patterns: [optional local env file with checked-in fallback, dry-run env parity]
key-files:
  created: []
  modified: [docker-compose.yml, .env.example, tests/ops/test_docker_scheduler.py, app/ops/dry_run.py, tests/conftest.py]
key-decisions:
  - "Compose now tolerates a missing local .env by reading .env.example as a clean-checkout fallback, preserving the repo's documented operator path."
  - "Dry-run env overrides must include schedule timezone so tests and operator tooling share the same scheduler configuration surface."
patterns-established:
  - "Operator-facing Docker defaults use Compose service DNS (`postgres`) instead of host-local addresses."
  - "Shared dry-run helpers should export every scheduler env used by tests rather than relying on test-only patches."
requirements-completed: [TBD-13-01, TBD-13-02]
duration: 4min
completed: 2026-04-02
---

# Phase 13: Replace Host Cron Scripts With A Docker-Native Scheduler Summary

**Tightened the Compose runtime and env defaults so the Docker-native scheduler path renders cleanly and preserves the existing dedupe behavior**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-02T05:52:00Z
- **Completed:** 2026-04-02T05:56:04Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Updated Compose and `.env.example` so the Docker stack resolves against `postgres` and renders on a clean checkout.
- Extended ops coverage to lock the Docker-native env defaults into the test suite.
- Moved the scheduler timezone env into the shared dry-run helper so route and integration tests use the same runtime contract as operators.

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace the single-service Compose file with the app-managed scheduler runtime** - `27fb5b4` (feat)
2. **Task 2: Bring the restored scheduling tests green without changing the dedupe ownership boundary** - `a8a1044` (fix)

## Files Created/Modified
- `docker-compose.yml` - uses optional local env loading with a checked-in fallback and keeps the three-service runtime intact
- `.env.example` - points database and trigger defaults at the Compose-native runtime
- `tests/ops/test_docker_scheduler.py` - locks the Docker-native env defaults into the ops contract
- `app/ops/dry_run.py` - exports schedule timezone through the shared dry-run helper
- `tests/conftest.py` - drops the test-only timezone workaround

## Decisions Made
- Used `.env.example` as a fallback `env_file` source so `docker compose config` works before an operator creates a private `.env`.
- Kept all scheduled dedupe behavior inside the existing app/database path; the only runtime changes in this plan were configuration and test harness alignment.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Compose, env defaults, and dedupe verification are aligned for the Docker-native runtime.
- README, docs drift coverage, and the old host-cron scripts are the remaining blockers to complete Phase 13.

---
*Phase: 13-replace-host-cron-scripts-with-a-docker-native-scheduler*
*Completed: 2026-04-02*
