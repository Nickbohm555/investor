# Phase 6: Replace LangGraph With A Custom Workflow Engine - Research

**Researched:** 2026-03-31
**Domain:** app-owned workflow orchestration, approval state handling, and restart-safe persistence in a FastAPI/SQLAlchemy service
**Confidence:** MEDIUM

## User Constraints

No `CONTEXT.md` exists for this phase.

Locked constraints from roadmap, requirements, and project docs:
- Keep the existing Python/FastAPI/Postgres direction and reuse the current repository shape.
- The app must own workflow execution, approval handling, and restart-safe step transitions without LangGraph, checkpointers, or resume semantics.
- Approval may pre-stage Alpaca orders, but must not auto-submit live trades without final broker-side confirmation.
- Cron remains repo-managed; do not introduce a separate scheduler service.
- Preserve restart-safe trigger, approval, and broker-prestage coverage after the cutover.

## Summary

Phase 6 should be planned as a targeted refactor of the current runtime, not as a greenfield workflow-platform build. The repo already has most of the durable primitives needed for an app-owned engine: persisted `runs`, `recommendations`, `approval_events`, `state_transitions`, broker artifacts, and a JSON `state_payload` field in the ORM model. What remains LangGraph-shaped is the terminology and control contract around `thread_id`, `langgraph_checkpointer_url`, `resume_command`, `resuming`, and the idea that approval “replays” a paused payload. The code in `app/graph/workflow.py` is already a custom class with `invoke()` and `resume()` methods; the real cutover is to formalize that into an explicit persisted step engine and remove the leftover checkpointer/thread semantics cleanly.

The strongest planning implication is that Phase 6 needs both code refactoring and migration work. The checked-in `investor.db` still has an older `runs` schema and there are two sibling Alembic `0002_*` revisions off the same base. Historical or operator databases may therefore carry stale fields and stale terminology even if the live tests still pass on `Base.metadata.create_all()`. The plan should include one wave for engine extraction and behavior-preserving tests, one wave for schema/env/dependency cleanup, and one wave for final terminology and docs removal.

**Primary recommendation:** Replace the current `start_run()/resume_run()` contract with a thin persisted step dispatcher keyed by `runs.current_step`, keep SQLAlchemy transactions as the single state boundary, and remove LangGraph-era fields only behind explicit schema/env migration steps.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | 0.135.2 | HTTP routes, health, trigger, and approval entrypoints | Already the app boundary; official lifespan support fits runtime composition |
| `sqlalchemy` | 2.0.48 | Transactions, ORM persistence, and session scope | Best fit for explicit step transitions and atomic state writes |
| `alembic` | 1.18.4 | Schema migration and data-shape evolution | Required for removing/renaming persisted LangGraph-era fields safely |
| `pydantic-settings` | 2.13.1 | Environment-backed runtime settings | Keeps env migration explicit and typed |

Verified versions and latest upload dates from PyPI JSON on 2026-03-31:
- `fastapi` 0.135.2 — uploaded 2026-03-23
- `sqlalchemy` 2.0.48 — uploaded 2026-03-02
- `alembic` 1.18.4 — uploaded 2026-02-10
- `pydantic-settings` 2.13.1 — uploaded 2026-02-19

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `psycopg[binary]` | 3.3.3 | Postgres driver | Keep for Postgres runtime and migration execution |
| `httpx` | 0.28.1 | Quiver, Alpaca, and OpenAI-compatible adapters | Keep external calls at the edge; do not move them into the engine core |
| `itsdangerous` | 2.2.0 | Signed approval tokens | Keep token signing separate from workflow state |
| `pytest` | 9.0.2 | Unit, integration, and dry-run coverage | Existing suite already proves restart-safe flows |

Verified versions and latest upload dates from PyPI JSON on 2026-03-31:
- `psycopg` 3.3.3 — uploaded 2026-02-18
- `httpx` 0.28.1 — uploaded 2024-12-06
- `itsdangerous` 2.2.0 — uploaded 2024-04-16
- `pytest` 9.0.2 — uploaded 2025-12-06

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Thin app-owned step engine | Keep `langgraph` + `langgraph-checkpoint-postgres` | Conflicts with the phase goal and preserves thread/checkpointer semantics the roadmap explicitly wants gone |
| Thin app-owned step engine | Temporal / Prefect / Celery | Overkill for a local-first, repo-scheduled, request-driven workflow; adds infra and operational surface the project explicitly avoids |
| Explicit SQLAlchemy state transitions | Rebuild generic DAG replay/checkpoint semantics | Recreates LangGraph complexity instead of removing it |

**Installation:**
```bash
pip uninstall -y langgraph langgraph-checkpoint-postgres
pip install -e .
```

After the dependency change, `pyproject.toml` should keep the FastAPI/SQLAlchemy/Alembic/httpx/itsdangerous/psycopg/pydantic-settings/pytest stack and remove the LangGraph packages.

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── workflows/
│   ├── engine.py         # load run, dispatch current step, persist next step/status
│   ├── steps.py          # step handlers: research, memo, await_approval, broker_prestage, reject
│   └── state.py          # step/result DTOs serializable to JSON
├── services/
│   ├── approvals.py      # token verification + idempotent approval event recording
│   ├── broker_prestage.py
│   └── run_service.py
├── repositories/
│   ├── runs.py
│   └── broker_artifacts.py
└── api/
    └── routes.py         # trigger and approval routes call the engine, not a graph runtime
```

### Pattern 1: Persisted Step Dispatcher
**What:** Store the workflow cursor in app-owned fields like `current_step`, `status`, and JSON-safe step data, then dispatch the next handler from application code.
**When to use:** Every trigger, approval, and broker-prestage transition.
**Example:**
```python
# Source: SQLAlchemy transaction pattern
# https://docs.sqlalchemy.org/en/21/orm/session_transaction.html

def advance_run(session_factory, run_id: str, event: str | None = None) -> dict:
    with session_factory.begin() as session:
        run = session.get(RunRecord, run_id)
        handler = STEP_HANDLERS[run.current_step]
        result = handler(run=run, event=event, session=session)
        run.current_step = result.next_step
        run.status = result.status
        run.state_payload = result.state_payload
        return {"run_id": run.run_id, "status": run.status, "current_step": run.current_step}
```

### Pattern 2: Approval As External Event, Not Replay
**What:** Approval route verifies the token, records one approval event, and advances the persisted run to the next step. It should not deserialize a paused runtime blob and pretend to “resume” a hidden engine.
**When to use:** All approve/reject paths.
**Example:**
```python
# Source: repo-aligned pattern built on SQLAlchemy session.begin()
# https://docs.sqlalchemy.org/en/21/orm/session_transaction.html

def apply_review_decision(payload, token_id: str) -> dict:
    with session_factory.begin() as session:
        run = session.get(RunRecord, payload.run_id)
        ensure_run_is_decidable(run)
        ensure_token_not_replayed(session, token_id)
        record_approval_event(session, run_id=run.run_id, decision=payload.decision, token_id=token_id)
        queue_event(session, run_id=run.run_id, event=f"approval:{payload.decision}")
    return engine.advance(run_id=payload.run_id, event=f"approval:{payload.decision}")
```

### Pattern 3: Lifespan-Owned Runtime Composition
**What:** Compose engine dependencies once at startup and keep routes thin.
**When to use:** `create_app()` composition and tests.
**Example:**
```python
# Source: FastAPI lifespan docs
# https://fastapi.tiangolo.com/advanced/events/

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.workflow_engine = WorkflowEngine(session_factory=session_factory, settings=settings)
    yield

app = FastAPI(lifespan=lifespan)
```

### Anti-Patterns to Avoid
- **Mini-LangGraph rebuild:** Do not replace LangGraph with another replay/checkpoint abstraction that still depends on hidden cursors and opaque resume payloads.
- **Two sources of truth:** Do not keep both explicit run-step fields and a second “real” state machine inside `state_payload`.
- **Persisting Python model instances into JSON:** Keep `state_payload` JSON-native so approval/restart paths do not need ad hoc model reconstruction.
- **Side effects before durable transition:** Never send mail or create broker artifacts before the run row and transition rows reflect the step boundary.
- **Route-level orchestration:** Routes should validate and call the engine. They should not assemble workflow control logic inline.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Durable DB transactions | Custom transaction wrappers | SQLAlchemy `Session.begin()` / `sessionmaker.begin()` | Official pattern already handles commit/rollback boundaries cleanly |
| Schema evolution | Ad hoc SQL scripts | Alembic revisions and merges | Phase 6 includes field removal/rename risk and existing revision drift |
| Approval token crypto | Custom HMAC serializer | `itsdangerous` | Existing implementation already covers signed, expiring tokens |
| HTTP transport stack | Engine-managed sockets/retries | Existing `httpx` edge adapters | Keeps workflow core deterministic and testable |
| General replay/checkpoint runtime | Homegrown DAG/checkpointer layer | Thin step dispatcher over persisted run rows | The phase goal is app ownership, not recreating LangGraph features |

**Key insight:** The custom engine should be intentionally narrow. Hand-roll the domain-specific step dispatcher, not generic orchestration infrastructure that existing libraries already solve better.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `investor.db` exists in the repo root and its `runs` table is on an older schema with 0 rows and no `state_payload` column. Current ORM/model code expects `thread_id`, `approval_status`, `current_step`, and `state_payload`; operator Postgres databases may also contain historical `thread_id`, `resuming`, and `resume_command`-shaped values. | **Data migration + code edit.** Add a real Alembic path that reconciles schema drift first, then migrate or archive LangGraph-era fields/statuses before code stops reading them. |
| Live service config | None verified in external services on this machine. Cron and app behavior are repo-managed; no UI-managed LangGraph config source was found. | **None verified.** Keep phase scoped to repo/app config unless operator surfaces external service state. |
| OS-registered state | `crontab -l` returned no installed cron entries on this machine. Repo cron scripts target HTTP trigger routes and do not embed LangGraph-specific names. | **None on this machine.** If operator machines have installed cron jobs, only endpoint/env compatibility matters. |
| Secrets/env vars | `.env.example` still defines `INVESTOR_LANGGRAPH_CHECKPOINTER_URL`. `app/config.py` still exposes `langgraph_checkpointer_url`. The current shell had no `INVESTOR_` vars set, so live env usage could not be inspected directly. | **Code edit + operator env migration.** Remove the setting from config/docs and tell operators to delete or ignore the env var when upgrading. |
| Build artifacts | `pyproject.toml` still declares `langgraph` and `langgraph-checkpoint-postgres`. Any editable install or virtualenv built from this repo will continue to install those packages until dependencies are changed. `investor.db` is also a stale built/runtime artifact relative to current models. | **Code edit + reinstall.** Remove the dependencies, reinstall the package, and either migrate or replace stale local DB artifacts. |

**Nothing found in category:** Live service config and OS-registered state showed no LangGraph-specific runtime state on this machine.

## Common Pitfalls

### Pitfall 1: Dual State Machine Drift
**What goes wrong:** `runs.status/current_step` says one thing while `state_payload` implies another.
**Why it happens:** Planning preserves old replay-style payloads while also introducing explicit step fields.
**How to avoid:** Define one canonical engine contract: `current_step`, `status`, approval event rows, and JSON-safe step payload. Everything else is derivative.
**Warning signs:** Approval succeeds in tests but historical runs cannot be interpreted consistently from the database alone.

### Pitfall 2: Replay Semantics Sneak Back In
**What goes wrong:** Approval still loads a paused blob and calls a fake `resume()` API, just with new class names.
**Why it happens:** The current `ApprovalService` already deserializes `run.state_payload` and calls `runtime.resume_run(...)`; it is easy to rename that path instead of replacing it.
**How to avoid:** Make approval emit an external event into the run row and let the engine dispatch the next persisted step.
**Warning signs:** New code still talks about `resume`, `thread_id`, `resume_command`, or “paused workflow payload.”

### Pitfall 3: Alembic Drift Blocks Real Upgrades
**What goes wrong:** Fresh tests pass because `Base.metadata.create_all()` creates the latest tables, but real operator databases cannot upgrade cleanly.
**Why it happens:** The repo already has two sibling `0002_*` revisions and the checked-in SQLite file is behind the ORM schema.
**How to avoid:** Add migration reconciliation early in the phase and test upgrade paths against a pre-Phase-6 database shape.
**Warning signs:** Only SQLite-in-memory tests pass; operator DBs require manual deletes or dropped tables.

### Pitfall 4: Non-Idempotent Side Effects Cross Step Boundaries
**What goes wrong:** Mail send or broker prestage repeats on retry or partial failure.
**Why it happens:** The engine writes side effects and transitions in the wrong order or without an explicit terminal artifact contract.
**How to avoid:** Persist the boundary first, then execute the side effect with deterministic identifiers and replay-safe guards.
**Warning signs:** Duplicate broker artifacts, duplicate mail sends, or state transitions that skip intermediate statuses.

## Code Examples

Verified patterns from official sources:

### Transactional Session Boundary
```python
# Source: https://docs.sqlalchemy.org/en/21/orm/session_transaction.html

Session = sessionmaker(engine)

with Session.begin() as session:
    session.add(run)
    session.add(transition)
```

### FastAPI Lifespan Composition
```python
# Source: https://fastapi.tiangolo.com/advanced/events/

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.workflow_engine = WorkflowEngine(...)
    yield

app = FastAPI(lifespan=lifespan)
```

### Pydantic Settings Env-File Configuration
```python
# Source: https://docs.pydantic.dev/latest/api/pydantic_settings/

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVESTOR_")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangGraph durable execution via checkpointer + `thread_id` + `Command(resume=...)` | App-owned persisted step engine using explicit run-step fields and domain events | Current LangGraph docs still center durable execution on checkpointers and thread IDs as of 2026-03-31 | Phase 6 should remove those concepts from runtime code, env, docs, and persisted state |
| Hidden replay cursor in runtime state | Database-readable workflow cursor in `current_step` plus explicit status/transition rows | Current repo already stores app-owned run and transition rows | Makes approval/restart behavior auditable without understanding graph internals |
| Route-triggered “resume” of paused payload | Approval treated as an external event that advances a stored step | Required by the Phase 6 roadmap goal | Removes dependence on paused-state payload replay semantics |

**Deprecated/outdated:**
- `INVESTOR_LANGGRAPH_CHECKPOINTER_URL`: outdated once the app owns orchestration completely.
- `resume_command` strings in workflow payloads: outdated debug scaffolding tied to LangGraph semantics.
- README wording that calls the service “LangGraph-driven”: outdated and misleading relative to the implementation and Phase 6 goal.

## Open Questions

1. **Should historical runs be migrated or treated as archival-only?**
   - What we know: Current checked-in SQLite data has 0 rows, but operator Postgres data may contain old `thread_id`/status payloads.
   - What's unclear: Whether the operator needs old runs to remain approval-compatible after the cutover.
   - Recommendation: Decide this before plan breakdown. If historical runs matter, add an explicit data-migration task; if not, archive old rows and migrate forward-only.

2. **Do we remove `thread_id` entirely or rename it to a neutral cursor field?**
   - What we know: Success criteria reject LangGraph naming and resume semantics, and current tests assert thread reuse heavily.
   - What's unclear: Whether any non-LangGraph use remains for a stable execution cursor.
   - Recommendation: Prefer removing it from the public/runtime contract. If a stable cursor is still valuable internally, rename it in the same phase and stop exposing LangGraph terminology.

3. **Should broker prestage remain synchronous in the approval request?**
   - What we know: The current product is local-first, request-driven, and does not want a separate scheduler/worker service.
   - What's unclear: Whether future latency or retries justify a background queue now.
   - Recommendation: Keep it synchronous in Phase 6. Model it as the next engine step, but do not add a worker system in this phase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/graph/test_workflow.py tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-01 | Runtime no longer depends on LangGraph naming/config/checkpointer concepts | unit + integration | `python -m pytest tests/graph/test_workflow.py tests/services/test_persistence.py -q` | ✅ |
| SC-02 | Approval and rejection advance app-owned persisted steps instead of replaying paused payload state | integration | `python -m pytest tests/integration/test_hitl_resume.py tests/api/test_routes.py -q` | ✅ |
| SC-03 | Restart-safe trigger, approval, and broker-prestage flows remain covered after cutover | integration + ops | `python -m pytest tests/integration/test_broker_prestage.py tests/ops/test_dry_run.py -q` | ✅ |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/graph/test_workflow.py tests/api/test_routes.py tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py -q`
- **Per wave merge:** `python -m pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Migration-path test proving Phase-5 schema upgrades cleanly into the Phase-6 schema, including the duplicate-`0002` Alembic situation
- [ ] Engine-focused tests that remove assertions on `resume_command`, `langgraph_checkpointer_url`, and LangGraph-specific status names while preserving restart-safety
- [ ] Approval-path tests that assert the route advances persisted steps directly rather than reconstructing model instances from `state_payload`

## Sources

### Primary (HIGH confidence)
- PyPI JSON: https://pypi.org/pypi/fastapi/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/sqlalchemy/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/alembic/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/pydantic-settings/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/httpx/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/itsdangerous/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/psycopg/json — current version and upload date
- PyPI JSON: https://pypi.org/pypi/pytest/json — current version and upload date
- SQLAlchemy transactions docs: https://docs.sqlalchemy.org/en/21/orm/session_transaction.html — transaction scope and `Session.begin()` patterns
- SQLAlchemy session basics: https://docs.sqlalchemy.org/en/20/orm/session_basics.html — session lifecycle guidance
- FastAPI lifespan docs: https://fastapi.tiangolo.com/advanced/events/ — recommended startup/shutdown composition
- Alembic branches docs: https://alembic.sqlalchemy.org/en/latest/branches.html — multiple-head / merge guidance
- Pydantic settings docs: https://docs.pydantic.dev/latest/api/pydantic_settings/ — env-file and env-prefix configuration
- LangGraph durable execution docs: https://docs.langchain.com/oss/python/langgraph/durable-execution — current checkpointer/thread durability model
- LangGraph interrupts docs: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop — current `interrupt()` / `Command(resume=...)` behavior

### Secondary (MEDIUM confidence)
- Repository inspection of `app/graph/runtime.py`, `app/graph/workflow.py`, `app/services/approvals.py`, `app/db/models.py`, `app/db/migrations/versions/`, `README.md`, `.env.example`, and current tests — used to map actual migration surface and existing behavior

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - current versions verified against PyPI JSON and patterns verified against official docs
- Architecture: MEDIUM - the recommended engine shape is strongly grounded in the repo and official transaction/lifespan guidance, but the custom engine contract itself is app-specific
- Pitfalls: HIGH - based on official LangGraph semantics, official Alembic branch behavior, and directly observed repo state

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
