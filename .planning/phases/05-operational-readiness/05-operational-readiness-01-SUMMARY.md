---
phase: 05-operational-readiness
plan: 01
subsystem: infra
tags: [fastapi, readiness, dry-run, openai, quiver, alpaca, testing]
requires:
  - phase: 04-hitl-and-broker-prestage
    provides: broker prestage persistence and approval resume flow
provides:
  - startup readiness validation with operator-facing diagnostics
  - env-backed research adapter for normal runtime composition
  - deterministic dry-run command covering trigger to broker prestage
affects: [README, env-template, operations, tests]
tech-stack:
  added: []
  patterns:
    - explicit runtime doubles in tests and dry-run harnesses
    - FastAPI lifespan readiness gating
key-files:
  created:
    - app/ops/readiness.py
    - app/ops/dry_run.py
    - app/services/research_llm.py
    - tests/ops/test_readiness.py
    - tests/services/test_research_llm.py
    - tests/ops/test_dry_run.py
  modified:
    - app/config.py
    - app/main.py
    - tests/conftest.py
    - tests/api/test_routes.py
key-decisions:
  - "Normal app composition now uses env-backed OpenAI and Quiver configuration; deterministic doubles are injected only in tests and the dry-run harness."
  - "Readiness rejects placeholder operational values and broker-mode/base-url mismatches before the app serves requests."
patterns-established:
  - "Operational checks live in app/ops/readiness.py and run both at app composition time and in FastAPI lifespan."
  - "Repo-owned dry-run proof uses a local SQLite database, captured memo text, and explicit dependency doubles."
requirements-completed: [OPER-01, OPER-02]
duration: 8min
completed: 2026-03-31
---

# Phase 05: Operational Readiness Summary

**Startup now blocks on invalid operational config, the normal runtime path uses env-backed research wiring, and one repo-owned dry-run command proves trigger-to-prestage locally.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-31T15:59:58.618Z
- **Completed:** 2026-03-31T16:07:30Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Added readiness validation that rejects placeholder env values, mode/base-url mismatches, and broken session bindings with aggregated diagnostics.
- Replaced the default static research and Quiver doubles with an env-backed `HttpResearchLLM` adapter and explicit runtime seams.
- Added `python -m app.ops.dry_run`, which runs the scheduled trigger path, captures the approval URL from the memo, follows it, and verifies persisted broker artifacts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create failing readiness and dry-run coverage around the exact operational contract** - `e249fe1` (`test`)
2. **Task 2: Implement the FastAPI readiness gate, env-backed runtime composition, and deterministic dry-run command** - `cc326aa` (`feat`)

## Files Created/Modified

- `app/ops/readiness.py` - readiness error aggregation and startup guard helpers
- `app/ops/dry_run.py` - deterministic local trigger-to-prestage smoke command
- `app/services/research_llm.py` - env-backed HTTP research adapter
- `app/main.py` - readiness-gated FastAPI composition with explicit runtime seams
- `app/config.py` - OpenAI runtime settings surfaced in config
- `tests/ops/test_readiness.py` - readiness contract coverage
- `tests/services/test_research_llm.py` - HTTP adapter and app composition coverage
- `tests/ops/test_dry_run.py` - CLI dry-run proof coverage
- `tests/conftest.py` - explicit test doubles for Quiver and research seams
- `tests/api/test_routes.py` - explicit route-test doubles plus readiness-safe health check

## Decisions Made

- Normal runtime composition no longer invents default Quiver or LLM doubles; tests and dry-run paths must inject them explicitly.
- Placeholder values remain visible in `Settings` defaults so the operator sees the required variables, but readiness blocks startup until they are replaced.
- The dry-run path proves the approval loop by parsing the memo text rather than introducing a separate operator-only callback mechanism.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rewired existing tests to inject explicit research and Quiver doubles**
- **Found during:** Task 2
- **Issue:** Existing route and broker-prestage tests relied on the removed hidden runtime doubles and started making live Quiver HTTP requests.
- **Fix:** Updated shared test harnesses to inject `ResearchNode` and `httpx.MockTransport` explicitly.
- **Files modified:** `tests/conftest.py`, `tests/api/test_routes.py`
- **Verification:** `python -m pytest tests/api/test_routes.py tests/integration/test_broker_prestage.py -q`
- **Committed in:** `cc326aa`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to preserve the new explicit-runtime contract without reintroducing hidden defaults.

## Issues Encountered

- The first green implementation broke existing tests because they had been depending on implicit runtime doubles. The harness now injects those doubles explicitly, which matches the new production contract.

## User Setup Required

None - no external service configuration required for this plan's local verification path.

## Next Phase Readiness

- README and `.env.example` can now document the real startup and dry-run surfaces without guessing hidden behavior.
- The documented Postgres smoke path is still unproven on this machine because the local `localhost:5432` service rejected the documented credentials.

---
*Phase: 05-operational-readiness*
*Completed: 2026-03-31*
