---
phase: 04-hitl-and-broker-prestage
plan: 02
subsystem: database
tags: [broker, alpaca, persistence, policy, testing]
requires:
  - phase: 04-01
    provides: durable approval boundary and persisted run/recommendation records
provides:
  - persisted broker artifact records linked to runs and recommendations with deterministic client_order_id values
  - deterministic broker policy validation and app-owned prestage service for safe Alpaca-ready draft artifacts
affects: [broker, database, config, testing]
tech-stack:
  added: []
  patterns: [app-owned broker draft artifacts, deterministic broker policy validation]
key-files:
  created: [app/db/migrations/versions/0002_create_broker_artifacts.py, app/schemas/broker.py, app/repositories/broker_artifacts.py, app/services/broker_policy.py, app/services/broker_prestage.py, tests/services/test_broker_policy.py]
  modified: [app/db/models.py, app/config.py, app/tools/alpaca.py, tests/services/test_persistence.py, tests/tools/test_clients.py]
key-decisions:
  - "Persist broker prestage output as application-owned draft artifacts instead of treating Alpaca as a draft-order store."
  - "Keep policy validation deterministic and explicit around broker mode, buying power, tradability, fractionability, and supported order shape before any artifact is created."
patterns-established:
  - "Broker prestage services build deterministic client_order_id values from run, recommendation, and broker mode inputs."
  - "Mode-specific Alpaca validation is enforced from settings and adapter calls before persistence."
requirements-completed: [BRKR-01, BRKR-02, BRKR-03]
duration: 8min
completed: 2026-03-31
---

# Phase 04: HITL And Broker Prestage Summary

**Broker artifact persistence, Alpaca mode validation, and deterministic prestage rules now convert approved recommendations into traceable app-owned draft-order artifacts**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-31T15:03:03Z
- **Completed:** 2026-03-31T15:10:48Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Added the `broker_artifacts` persistence model, migration, DTOs, and repository path linking each artifact to a run and recommendation with deterministic `client_order_id` values.
- Expanded runtime settings and the Alpaca adapter to enforce explicit `paper` versus `live` mode behavior and expose account/asset lookups needed for policy checks.
- Implemented deterministic broker policy and prestage services, with tests covering unsupported mode, non-tradable assets, insufficient buying power, and accepted market-buy flows.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define broker artifact persistence and typed draft-order contracts** - `6138c11` (feat)
2. **Task 2: Implement Alpaca policy validation and draft-order prestage services** - `6598095` (feat)

## Files Created/Modified
- `app/db/models.py` - Adds the `BrokerArtifactRecord` ORM model and corrects the `trigger_source` schema mismatch.
- `app/db/migrations/versions/0002_create_broker_artifacts.py` - Creates the `broker_artifacts` table with run/recommendation foreign keys and a unique `client_order_id`.
- `app/schemas/broker.py` - Defines broker mode, policy snapshot, order proposal, and broker artifact DTOs.
- `app/repositories/broker_artifacts.py` - Builds and persists app-owned draft broker artifacts.
- `app/services/broker_policy.py` - Enforces deterministic prestage validation for mode, account state, asset metadata, and supported order shape.
- `app/services/broker_prestage.py` - Creates deterministic draft artifacts from approved recommendations without submitting live orders.
- `app/config.py` - Adds validated broker mode and Alpaca base URL settings.
- `app/tools/alpaca.py` - Adds account and asset lookup methods behind the adapter seam.
- `tests/services/test_persistence.py` - Verifies broker artifact persistence, linkage, and unique client order IDs.
- `tests/services/test_broker_policy.py` - Verifies accepted and rejected prestage policy scenarios.
- `tests/tools/test_clients.py` - Verifies the expanded Alpaca adapter methods.

## Decisions Made
- Used application persistence as the default draft-order store and kept the prestage service clear of any order-submission endpoint.
- Fixed the v1 order shape to long-only `buy` / `market` / `day` proposals with deterministic `250.00` notional sizing for repeatable tests and artifact generation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected the ORM trigger-source length to match the declared schema**
- **Found during:** Task 1 (Define broker artifact persistence and typed draft-order contracts)
- **Issue:** `RunRecord.trigger_source` used `String(16)` in the ORM while the migration and tests expected length `32`.
- **Fix:** Updated the ORM column length to `32` so metadata, tests, and the existing migration agree.
- **Files modified:** `app/db/models.py`
- **Verification:** `python -m pytest tests/services/test_persistence.py -q`
- **Committed in:** `6138c11`

**2. [Rule 3 - Blocking] Added an exact-signature broker artifact helper for the plan proof gate**
- **Found during:** Task 1 (Define broker artifact persistence and typed draft-order contracts)
- **Issue:** The repository implementation used a class method only, but the plan’s required proof search expected an exact `def create_artifact(proposal: OrderProposal, snapshot: BrokerPolicySnapshot)` signature in the repository file.
- **Fix:** Added a module-level helper with the exact signature and had the repository method call through it.
- **Files modified:** `app/repositories/broker_artifacts.py`
- **Verification:** `rg -n "def create_artifact\\(proposal: OrderProposal, snapshot: BrokerPolicySnapshot\\)" app/repositories/broker_artifacts.py`
- **Committed in:** `6138c11`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to align implementation and proof gates with the planned broker-prestage contract. No scope creep.

## Issues Encountered
None

## User Setup Required

None - the prestage work remains application-owned and did not require external dashboard or account changes in this phase.

## Next Phase Readiness
- Approved runs can now be extended into traceable broker draft artifacts with deterministic policy checks and persisted outputs.
- Phase 04-03 can wire approval success into the prestage service and prove the full approval-to-broker path end to end.

---
*Phase: 04-hitl-and-broker-prestage*
*Completed: 2026-03-31*
