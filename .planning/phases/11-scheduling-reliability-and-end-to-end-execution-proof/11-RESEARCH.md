# Phase 11: Scheduling Reliability And End-To-End Execution Proof - Research

**Researched:** 2026-03-31
**Domain:** Cron-based scheduling reliability, timezone-safe market-open cadence, and end-to-end workflow proof from scheduled trigger through broker submission
**Confidence:** MEDIUM

## Summary

Phase 11 should not introduce a new scheduler or a second execution path. The repo already has the correct core shape for this phase: repo-managed cron scripts, application-level scheduled-run dedupe in Postgres, timezone-aware schedule keys via `zoneinfo`, deterministic mail/approval/broker-prestage seams, and a dry-run harness that proves scheduled trigger through approval. The correct planning move is to extend those same seams to the Phase 9 and Phase 10 confirmation/submission contracts, then harden the cron configuration path so a real `7:00am ET` schedule is installed from repo config instead of being hard-coded in shell scripts.

The main gap is not basic scheduling. It is contract continuity across phases. Today the system stops at `broker_prestaged`: `app/workflows/engine.py` only supports `approval:approve` and `approval:reject`, `app/tools/alpaca.py` only reads account and asset data, and there is no execution-confirmation or order-submission route. That means Phase 11 planning must explicitly depend on Phase 9 and Phase 10 artifacts landing first, or define those exact seams if planning is being done ahead of implementation.

For reliability, the planner should treat timezone handling as a real risk area. The current app uses `ZoneInfo("America/New_York")` correctly for schedule keys, but the cron install script is still hard-coded to `30 8 * * 1-5`. A robust Phase 11 plan should wire `INVESTOR_SCHEDULE_CRON_EXPRESSION` into cron install/status tests, decide whether to use `CRON_TZ=America/New_York` in the managed cron block, and keep dedupe in the database rather than shell locking. End-to-end proof should stay deterministic and repo-local first: extend the existing `TestClient` plus subprocess-based operational harness so it covers scheduled trigger, memo link extraction, approval, explicit execution confirmation, and submitted-order persistence/status updates using paper-safe doubles.

**Primary recommendation:** Extend the existing cron + FastAPI + pytest proof path; do not build a new scheduler, and do not plan Phase 11 as complete until Phase 9/10 define a concrete confirmation-and-submission contract.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.2 | HTTP routes for scheduled trigger, approval, and future execution-confirmation endpoints | Already owns the operational workflow surface; official `TestClient` support keeps end-to-end tests simple |
| SQLAlchemy | 2.0.48 | Persist run state, dedupe keys, approval events, broker artifacts, and future submitted-order records | Existing run/audit truth already lives here; reliability should stay database-backed |
| pydantic-settings | 2.13.1 | Repo-configured env surface for cron expression, trigger URL/token, broker mode, and base URLs | Current settings model is the correct place to expose the 7:00am ET config path |
| pytest | 9.0.2 | Unit, API, ops, and integration coverage for scheduling and end-to-end proof | Existing suite is already organized around repo-local operational proofs |
| httpx | 0.28.1 | Transport doubles and external adapter testing for Quiver, SMTP-like seams, and Alpaca submission | FastAPI testing and external adapter isolation already rely on this style |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `zoneinfo` | stdlib (3.12+) | America/New_York schedule-key normalization and DST-safe application-side time logic | Use for all app-side market-date and ET conversions |
| Cron / crontab | host tool | Actual operator schedule installation and removal | Use for the real 7:00am ET install path because the project explicitly requires repo-managed cron |
| Alembic | 1.18.4 | Schema migration for any Phase 9-11 execution/submission tables or columns | Use if submitted-order or execution-confirmation state needs persistence changes |
| Alpaca Trading API | current official API | Order submission and order-status tracking after confirmation | Use via the existing adapter seam; keep paper/live separation explicit |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Repo-managed cron | APScheduler / Celery Beat / external scheduler service | Violates the project constraint to keep scheduling inside repo-managed cron artifacts |
| DB-backed scheduled dedupe | Shell lockfiles / `flock` | Easier to add, but weaker across retries and alternate trigger paths; the database uniqueness seam is already correct |
| Existing FastAPI `TestClient` + subprocess harness | Browser/E2E framework first | Higher overhead and lower determinism for this backend-heavy workflow; browser proof can stay optional until a real confirmation UI exists |

**Installation:**

```bash
pip install -e .
```

**Version verification:** Verified against PyPI JSON on 2026-03-31.

```bash
python -m pip index versions fastapi
python - <<'PY'
import json, urllib.request
for pkg in ["fastapi", "sqlalchemy", "pydantic-settings", "pytest", "httpx", "alembic"]:
    data = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json"))
    print(pkg, data["info"]["version"])
PY
```

Verified latest versions and latest upload timestamps:

| Package | Latest | Published |
|---------|--------|-----------|
| FastAPI | 0.135.2 | 2026-03-23 |
| SQLAlchemy | 2.0.48 | 2026-03-02 |
| pydantic-settings | 2.13.1 | 2026-02-19 |
| pytest | 9.0.2 | 2025-12-06 |
| httpx | 0.28.1 | 2024-12-06 |
| Alembic | 1.18.4 | 2026-02-10 |

## Architecture Patterns

### Recommended Project Structure

```text
app/
├── config.py                # env-backed schedule/broker/runtime settings
├── api/routes.py            # trigger, approval, and future execution-confirmation routes
├── services/scheduling.py   # ET schedule-key logic and scheduled-run dedupe
├── services/approvals.py    # approval-state enforcement
├── services/                # future execution-confirmation / submission policy services
├── tools/alpaca.py          # Alpaca account/asset/order adapter
├── workflows/engine.py      # persisted workflow transitions
└── ops/dry_run.py           # operator-proof harness
tests/
├── api/                     # route-level contracts
├── integration/             # restart-safe and multi-step proofs
└── ops/                     # cron/install/dry-run operational tests
scripts/
├── cron-install.sh          # installs managed cron block from repo config
├── cron-status.sh           # exposes installed schedule/log path status
├── cron-trigger.sh          # minimal shell wrapper that loads .env and POSTs the trigger
└── cron-remove.sh           # removes only managed block
```

### Pattern 1: Cron Is a Thin Trigger Wrapper, Not the Source of Truth

**What:** Keep cron responsible only for launching the scheduled HTTP trigger with env loading and append-only logging. Keep duplicate prevention and workflow branching in app/database code.

**When to use:** Always for this repo. The project constraint explicitly requires local cron, but Phase 3 already established that dedupe belongs in the application seam.

**Example:**

```python
# Repo pattern from app/services/scheduling.py
def create_or_get_scheduled_run(session, now=None, run_factory=None):
    schedule_now = now or datetime.now(tz=NEW_YORK)
    schedule_key = build_schedule_key(schedule_now)
    run = run_factory(schedule_key)
    session.add(run)
    try:
        session.commit()
        session.refresh(run)
        return run, False
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(RunRecord).where(RunRecord.schedule_key == schedule_key))
        if existing is None:
            raise
        return existing, True
```

### Pattern 2: ET Cadence Is Configuration, Market-Date Logic Is Application Code

**What:** Put the installed cron expression in settings and scripts, but continue to compute schedule keys and market dates inside Python using `ZoneInfo("America/New_York")`.

**When to use:** For any market-open or market-day behavior. Cron decides when to call; Python decides what market day the run belongs to.

**Example:**

```python
# Source: https://docs.python.org/3/library/zoneinfo.html
from datetime import datetime
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
now = datetime.now(tz=NEW_YORK)
market_date = now.astimezone(NEW_YORK).date().isoformat()
```

### Pattern 3: End-To-End Proof Uses Deterministic Doubles Through Real Route Boundaries

**What:** Use FastAPI `TestClient`, subprocess-launched ops harnesses, and adapter doubles to prove the full multi-step workflow without real external services.

**When to use:** For repo-local phase gating. Real cron or real Alpaca paper checks can remain secondary/manual validation.

**Example:**

```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
from fastapi.testclient import TestClient

client = TestClient(app)

def test_route():
    response = client.post("/runs/trigger/scheduled")
    assert response.status_code == 202
```

### Pattern 4: Submission Traceability Should Reuse `client_order_id`

**What:** Continue using deterministic broker correlation IDs and persist them through submission records/status updates instead of inventing a separate opaque mapping layer.

**When to use:** For the Phase 9/10/11 execution-confirmation and submitted-order path.

**Example:**

```python
# Existing repo pattern in app/services/broker_prestage.py
client_order_id = f"{run_id}-{recommendation_id}-{broker_mode}"
```

### Anti-Patterns to Avoid

- **Hard-coded cron expressions in scripts:** `scripts/cron-install.sh` currently hard-codes `30 8 * * 1-5`; Phase 11 should not leave the 7:00am ET path split across docs, env, and shell.
- **Cron-local duplicate protection:** Do not add shell lockfiles, PID files, or `flock` as the primary duplicate guard. The database uniqueness seam already solves the real problem.
- **New operational proof path:** Do not create a second “Phase 11 only” smoke command. Extend `python -m app.ops.dry_run` or add an adjacent ops harness that reuses the same runtime composition.
- **Pretending submission already exists:** There is no execution-confirmation or order-submission route today. Planning must call that out explicitly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ET timezone and DST handling | Custom offset math or hand-maintained EST/EDT rules | Python `zoneinfo` with `America/New_York` | Official IANA rules already handle ambiguous DST transitions correctly |
| Scheduler service | In-repo daemon, APScheduler sidecar, or background loop | Host cron managed by repo scripts | Matches project constraints and current operational model |
| Duplicate scheduled-run prevention | Shell lockfiles or ad hoc marker files | DB uniqueness on `schedule_key` plus application fetch-on-conflict | Survives retries, restarts, and non-cron trigger paths |
| API end-to-end proof | Manual click-only testing as the main gate | FastAPI `TestClient` + subprocess ops harness + doubles | Gives fast, repeatable, repo-local verification |
| Broker submission correlation | Separate mapping table without order IDs | Deterministic `client_order_id` and persisted broker records | Alpaca already supports client order IDs and order lookups by them |

**Key insight:** The repo already has the right seams. Phase 11 should compose and extend them, not replace them.

## Common Pitfalls

### Pitfall 1: Assuming `30 7 * * 1-5` Means 7:00am ET Everywhere

**What goes wrong:** Cron runs at 7:00 in the host's local timezone, not necessarily Eastern Time.

**Why it happens:** Cron interprets fields in the daemon's timezone unless a supported timezone override like `CRON_TZ` is used. The app's ET schedule key does not fix a wrongly timed cron fire.

**How to avoid:** Decide explicitly whether the managed cron block sets `CRON_TZ=America/New_York` or whether operator docs require the host timezone to be ET. Then test the generated crontab text.

**Warning signs:** The schedule key is correct for ET dates, but the job fires an hour early/late after DST or on non-ET hosts.

### Pitfall 2: Treating Cron Dedupe as Sufficient End-To-End Reliability

**What goes wrong:** Scheduling succeeds, but approval, confirmation, or submission still require hidden operator glue.

**Why it happens:** The system is only currently proven through `broker_prestaged`; the final confirmation and submit path are not yet implemented.

**How to avoid:** Make the Phase 11 proof start at `/runs/trigger/scheduled` and end at persisted submitted-order state or confirmed Alpaca response, not at memo delivery or broker prestage.

**Warning signs:** A test passes without ever exercising the future confirmation endpoint or order-submission adapter.

### Pitfall 3: Relying on Cron Alone for DST Semantics

**What goes wrong:** Jobs scheduled in ambiguous or skipped local times behave unexpectedly around DST transitions.

**Why it happens:** Cron evaluates matching wall-clock times, and official cron docs note skipped times will not run and repeated times can run twice.

**How to avoid:** Keep the target time at 7:00am ET, which is away from the DST rollover window, and keep market-date dedupe in the database.

**Warning signs:** Duplicate or missing scheduled runs around DST weekend when testing early-morning jobs or alternate cron expressions.

### Pitfall 4: Splitting Config Across Settings, Docs, and Shell Without Tests

**What goes wrong:** `.env.example`, `README.md`, readiness checks, and cron scripts drift apart.

**Why it happens:** Shell scripts are easy to hard-code while Python config evolves.

**How to avoid:** Add tests that assert cron install/status output reflects `INVESTOR_SCHEDULE_CRON_EXPRESSION` and the documented 7:00am ET path.

**Warning signs:** README says 7:00am ET, but installed crontab still shows `30 8 * * 1-5`.

## Code Examples

Verified patterns from official sources:

### Timezone-Aware Datetimes

```python
# Source: https://docs.python.org/3/library/zoneinfo.html
from zoneinfo import ZoneInfo
from datetime import datetime

dt = datetime.now(tz=ZoneInfo("America/New_York"))
```

### FastAPI Route Testing

```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
```

### Pytest Layout

```text
# Source: https://docs.pytest.org/en/stable/explanation/goodpractices.html
pyproject.toml
src/
tests/
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded shell schedule | Env/config-driven cron install path | Needed now for Phase 11 | Removes drift between docs, config, and installed crontab |
| Approval ends at broker prestage | Approval followed by explicit execution confirmation and submission | Planned for Phases 9-11 | Required to prove the true end-to-end operator flow |
| Manual cron spot-checks only | Automated cron script tests plus deterministic end-to-end ops harness | Already started in Phase 3/5; should expand in Phase 11 | Makes scheduling regressions cheap to catch |
| Broker artifact trace only | Broker artifact trace plus submitted-order trace/status | Planned for Phases 9-11 | Needed for trustworthy execution proof |

**Deprecated/outdated:**

- Hard-coded `30 8 * * 1-5` in [`scripts/cron-install.sh`](/Users/nickbohm/Desktop/Tinkering/investor/scripts/cron-install.sh) is outdated for this phase.
- Treating `broker_prestaged` as the end of the operational proof is outdated for this phase's success criteria.

## Open Questions

1. **What is the exact Phase 9 execution-confirmation surface?**
   - What we know: The roadmap requires a second explicit confirmation before order submission.
   - What's unclear: Whether that confirmation is a GET link, POST route, CLI step, or lightweight HTML form.
   - Recommendation: Lock this in Phase 9 planning first; Phase 11 should test the same operator-facing contract, not invent a temporary one.

2. **Should the managed cron block rely on `CRON_TZ=America/New_York`?**
   - What we know: Standard cron supports `CRON_TZ`, but host cron implementations can vary.
   - What's unclear: Whether the target operator environment is guaranteed to support it.
   - Recommendation: Plan one task to detect/document support and one fallback path if unsupported; do not leave timezone behavior implicit.

3. **What submitted-order state must persist locally after Alpaca accepts an order?**
   - What we know: Existing artifacts persist `client_order_id` and policy snapshots before submission.
   - What's unclear: The final schema for submitted order ID, status, timestamps, and reconciliation fields.
   - Recommendation: Reuse `client_order_id` as the correlation key and require explicit persisted submission records before calling Phase 11 complete.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.1.2 installed in repo environment; latest available 9.0.2 |
| Config file | [`pyproject.toml`](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml) |
| Quick run command | `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_dry_run.py tests/api/test_scheduling.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC11-01 | Repo config installs a real 7:00am ET cron path through managed scripts | ops/integration | `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_readiness.py -q` | ✅ partial |
| SC11-02 | Scheduled run, memo delivery, approval, execution confirmation, and submission work without hidden glue | integration/smoke | `python -m pytest tests/ops/test_dry_run.py tests/api/test_routes.py -q` | ❌ needs Phase 9/10 extension |
| SC11-03 | End-to-end tests cover scheduled run through submitted order behavior | integration | `python -m pytest tests/integration/test_scheduled_submission_flow.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ops/test_cron_scripts.py tests/api/test_scheduling.py -q`
- **Per wave merge:** `python -m pytest tests/ops/test_dry_run.py tests/integration/test_broker_prestage.py tests/api/test_routes.py -q`
- **Phase gate:** `python -m pytest -q` plus one explicit operational smoke command that exercises the scheduled-to-submitted flow

### Wave 0 Gaps

- [ ] `tests/integration/test_scheduled_submission_flow.py` — scheduled trigger -> memo -> approval -> confirmation -> submit
- [ ] `tests/api/test_execution_confirmation.py` — explicit confirmation endpoint semantics and duplicate/stale handling
- [ ] `tests/tools/test_alpaca_orders.py` — Alpaca order submission adapter and status parsing
- [ ] `app/ops/dry_run.py` or sibling ops harness update — final JSON must include submitted-order proof, not only `broker_prestaged`

## Sources

### Primary (HIGH confidence)

- https://docs.python.org/3/library/zoneinfo.html - `ZoneInfo` behavior, IANA timezone support, and DST ambiguity handling
- https://fastapi.tiangolo.com/tutorial/testing/ - official `TestClient` testing pattern
- https://docs.pytest.org/en/stable/explanation/goodpractices.html - pytest test layout and import guidance
- https://docs.alpaca.markets/docs/working-with-orders - Alpaca order submission, `client_order_id`, and order update patterns
- https://pypi.org/pypi/fastapi/json - current FastAPI version and publish date
- https://pypi.org/pypi/sqlalchemy/json - current SQLAlchemy version and publish date
- https://pypi.org/pypi/pydantic-settings/json - current pydantic-settings version and publish date
- https://pypi.org/pypi/pytest/json - current pytest version and publish date
- https://pypi.org/pypi/httpx/json - current httpx version and publish date
- https://pypi.org/pypi/alembic/json - current Alembic version and publish date

### Secondary (MEDIUM confidence)

- https://man7.org/linux/man-pages/man5/crontab.5.html - `CRON_TZ`, minute-level cron matching, and DST caveats; authoritative for standard cron behavior but host implementations can differ

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - mostly existing repo stack plus official docs and current package registry data
- Architecture: MEDIUM - existing codebase is clear, but Phases 9 and 10 are not planned yet, so final confirmation/submission seams are still inferred from roadmap intent
- Pitfalls: HIGH - directly supported by current code gaps plus official cron/timezone behavior

**Research date:** 2026-03-31
**Valid until:** 2026-04-07
