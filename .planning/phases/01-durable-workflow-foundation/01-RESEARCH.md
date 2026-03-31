# Phase 1: Durable Workflow Foundation - Research

**Researched:** 2026-03-31
**Domain:** Durable workflow orchestration, Postgres persistence, approval-state API semantics
**Confidence:** HIGH

## Summary

Phase 1 should move the app from a process-local prototype to a restart-safe workflow runtime built around LangGraph persistence plus explicit application records in Postgres. The local spec is consistent on this point: workflow durability and auditability are first-class requirements, and the current `app.state.workflow_store` approach in [app/main.py](/Users/nickbohm/Desktop/Tinkering/investor/app/main.py) and [app/api/routes.py](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py) is the exact gap this phase exists to close.

The implementation should not treat approval links as the source of truth. Signed tokens remain the transport, but the authoritative state must live in Postgres: run status, thread ID, recommendations, approval attempts, and state transitions. The approval endpoint should validate the token, load the persisted run, reject stale or duplicate attempts from persisted state, record the event, and resume the same LangGraph thread with the same `thread_id`.

This phase should also lock in a stricter boundary between two persistence concerns: LangGraph checkpoints for graph resume and SQLAlchemy-managed application tables for business records. Keep both in Postgres, but do not collapse them into one hand-rolled persistence layer.

**Primary recommendation:** Use LangGraph `interrupt()`/`Command(resume=...)` with `langgraph-checkpoint-postgres` for workflow durability, and add a SQLAlchemy repository/service layer that owns run records, approval events, recommendation rows, and transition logging.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RUNT-01 | Operator can trigger a daily run that persists workflow state and survives process restart | LangGraph persistence requires a checkpointer and stable `thread_id`; use persisted `run_id` + `thread_id`, compile the graph with `PostgresSaver`, and resume with the same config after app restart. |
| RUNT-02 | System stores run records, recommendation records, approval events, and state transitions in Postgres | Add repository services over SQLAlchemy models and migrations; persist application records separately from LangGraph checkpoint tables. |
| RUNT-03 | Operator receives explicit API responses for invalid, expired, stale, or duplicate approval attempts | Map token and run-state domain errors to FastAPI `HTTPException` or custom exception handlers with stable 4xx responses; add tests for each approval failure mode. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `langgraph` | `1.1.3` (published 2026-03-18) | Durable workflow runtime with interrupt/resume | Official docs make `interrupt()` + `thread_id` + checkpointer the standard HITL durability path. |
| `langgraph-checkpoint-postgres` | `3.0.5` (published 2026-03-18) | Postgres-backed checkpoint persistence | Official Postgres saver for production LangGraph durability. |
| `sqlalchemy` | `2.0.48` (published 2026-03-02) | ORM models, session management, repositories | Already present in repo; 2.x session patterns fit service/repository boundaries cleanly. |
| `alembic` | `1.18.4` (published 2026-02-10) | Schema migrations | Standard migration layer for SQLAlchemy-backed apps. |
| `psycopg[binary]` | `3.3.3` (published 2026-02-18) | Postgres driver | Required for reliable local Postgres connectivity and LangGraph Postgres saver support. |
| `fastapi` | `0.135.2` (published 2026-03-23) | API routes and exception mapping | Current repo framework; official error-handling model fits explicit approval responses. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic-settings` | `2.13.1` (published 2026-02-19) | Environment-backed settings | Keep configuration centralized for DB URLs, token TTL, and base URL. |
| `itsdangerous` | `2.2.0` (published 2024-04-16) | Signed expiring approval tokens | Keep token signing; pair it with persisted approval-state checks. |
| `pytest` | `9.0.2` (published 2025-12-06) | Test runner | Existing test framework; extend with restart-safe integration coverage. |
| `uvicorn` | Current repo dependency | ASGI runtime | Needed for local manual verification, but not a design decision driver for this phase. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `langgraph-checkpoint-postgres` | Hand-rolled serialized workflow state in app tables | Worse durability semantics, more edge cases, and duplicates what LangGraph already solves. |
| SQLAlchemy repositories | Raw SQL in route handlers | Faster to start, but increases coupling and makes transition/audit logging brittle. |
| FastAPI exception mapping | Ad hoc `dict` error returns in endpoints | Harder to standardize, document, and test. |

**Installation:**
```bash
pip install -U fastapi sqlalchemy alembic "psycopg[binary]" langgraph langgraph-checkpoint-postgres pydantic-settings itsdangerous pytest uvicorn
```

**Version verification:** verified against PyPI package metadata on 2026-03-31.

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── api/                  # FastAPI routes and exception handlers
├── db/                   # engine/session setup, models, migrations
├── repositories/         # run, recommendation, approval, transition persistence
├── services/             # orchestration-facing business services
├── graph/                # LangGraph state schema and workflow compile/resume logic
└── schemas/              # Pydantic DTOs for API and workflow payloads
```

### Pattern 1: Separate Checkpoint Persistence From Application Persistence
**What:** Store workflow checkpoints in LangGraph's Postgres saver, but store business/audit records in SQLAlchemy tables.
**When to use:** Always in this phase. The product spec explicitly requires both.
**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/persistence
config = {"configurable": {"thread_id": "run-123"}}
graph = builder.compile(checkpointer=checkpointer)
graph.invoke(initial_input, config=config)
```

### Pattern 2: Persist `run_id` And `thread_id` Together
**What:** Treat `run_id` as the product-level identifier and `thread_id` as the LangGraph resume pointer.
**When to use:** On trigger, before first graph invocation.
**Example:**
```python
run = run_repository.create_run(
    run_id=run_id,
    thread_id=thread_id,
    status="triggered",
)
graph.invoke({"run_id": run.run_id}, config={"configurable": {"thread_id": run.thread_id}})
```

### Pattern 3: Use Repository Services Inside Transaction Frames
**What:** Open short-lived SQLAlchemy sessions with `sessionmaker` and let service methods own transaction boundaries.
**When to use:** Route handlers, trigger flow, approval flow, transition logging.
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
SessionLocal = sessionmaker(engine, expire_on_commit=False)

with SessionLocal.begin() as session:
    repository = RunRepository(session)
    repository.mark_transition(run_id, "awaiting_approval", "approved")
```

### Pattern 4: Approval Route As Validation + Resume Adapter
**What:** The route should validate token, load persisted run state, reject invalid transitions, record the event, resume the graph, and map domain errors to 4xx responses.
**When to use:** `GET /approval/{token}`.
**Example:**
```python
payload = token_service.verify(token)
run = workflow_service.load_pending_run(payload.run_id)
result = workflow_service.resume_run(run, decision=payload.decision)
return result
```

### Pattern 5: Keep Side Effects After Interrupt Idempotent
**What:** LangGraph resumes the interrupted node from the start, so code before `interrupt()` can re-run.
**When to use:** Approval node and any node that can resume after restart.
**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/interrupts
from langgraph.types import Command, interrupt

def approval_node(state):
    decision = interrupt({"question": "Approve this action?"})
    return Command(goto="proceed" if decision else "cancel")
```

### Anti-Patterns to Avoid
- **Process-local workflow store:** `app.state.workflow_store` guarantees restart loss.
- **Approval token as source of truth:** token validity is not enough; persisted run status must still allow the transition.
- **Route handlers writing ORM directly everywhere:** duplicate persistence logic will drift and make audit logging inconsistent.
- **Combining checkpoint tables with business tables manually:** this recreates LangGraph persistence badly.
- **Embedding irreversible side effects before `interrupt()`:** resumed nodes can re-run pre-interrupt code.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Workflow pause/resume durability | Custom serialized workflow dicts in app tables | LangGraph + Postgres checkpointer | Handles checkpoints, resume semantics, and pending writes already. |
| Approval-token signing and expiry | Homemade HMAC token format | `itsdangerous` timed serializers | Standard signed/expiring token behavior already exists. |
| Migration bookkeeping | Manual `CREATE TABLE` scripts | Alembic revisions | Keeps schema changes auditable and repeatable. |
| API error shaping | Repeated inline `try/except` JSON dicts | FastAPI `HTTPException` and app-level exception handlers | Standard 4xx responses and testable semantics. |

**Key insight:** The complexity in this phase is not CRUD. It is correctness across restart, duplicate approval attempts, and state-machine boundaries. Use the libraries that already solve those parts.

## Common Pitfalls

### Pitfall 1: Re-running Side Effects On Resume
**What goes wrong:** Approval-related code sends email, writes duplicate rows, or replays broker handoff prep when the interrupted node resumes.
**Why it happens:** LangGraph resumes by restarting the interrupted node from the top.
**How to avoid:** Put side effects after the approval decision branch or guard them with persisted idempotency checks.
**Warning signs:** Duplicate approval events, repeated transitions, or repeated email/handoff artifacts for one run.

### Pitfall 2: Treating Token Validity As Approval Validity
**What goes wrong:** A valid signed token approves a run that is already completed, rejected, or expired from the product’s perspective.
**Why it happens:** Signature checks prove authenticity, not current business state.
**How to avoid:** Persist approval state and reject stale or duplicate transitions after loading the run.
**Warning signs:** Double-click approvals succeed or late approvals mutate finalized runs.

### Pitfall 3: Forgetting PostgresSaver Setup Requirements
**What goes wrong:** Checkpoint tables are not created or row access fails at runtime.
**Why it happens:** The Postgres saver requires `.setup()` on first use; manual connections also require `autocommit=True` and `row_factory=dict_row`.
**How to avoid:** Use `PostgresSaver.from_conn_string(...)` in app startup and run one-time setup in local provisioning.
**Warning signs:** Missing checkpoint tables or `TypeError` reading checkpoint rows.

### Pitfall 4: Leaving Tests On SQLite Happy Paths Only
**What goes wrong:** The suite stays green while production-intended Postgres and restart behavior remain unverified.
**Why it happens:** Current tests rely on in-memory SQLite and direct token construction.
**How to avoid:** Add restart-safe API tests and at least one Postgres-backed persistence path for this phase.
**Warning signs:** No test recreates the app between trigger and approval.

### Pitfall 5: Inconsistent Transition Logging
**What goes wrong:** Run status changes in one place but transition records are missing or misleading.
**Why it happens:** Status writes and transition writes are not owned by one service transaction.
**How to avoid:** Make a workflow service write both the new status and transition log in one transaction frame.
**Warning signs:** Run rows say `approved` or `completed` without a matching transition trail.

## Code Examples

Verified patterns from official sources:

### LangGraph Interrupt And Resume
```python
# Source: https://docs.langchain.com/oss/python/langgraph/interrupts
from langgraph.types import Command, interrupt

def approval_node(state):
    approved = interrupt("Do you approve this action?")
    return {"approved": approved}

config = {"configurable": {"thread_id": "thread-1"}}
graph.invoke({"input": "data"}, config=config)
graph.invoke(Command(resume=True), config=config)
```

### SQLAlchemy Session Factory And Transaction Scope
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(engine, expire_on_commit=False)

with SessionLocal.begin() as session:
    session.add(some_object)
```

### FastAPI Explicit 4xx Response
```python
# Source: https://fastapi.tiangolo.com/tutorial/handling-errors/
from fastapi import HTTPException

if run is None:
    raise HTTPException(status_code=404, detail="Run not found")
```

### Timed Token Verification
```python
# Source: https://itsdangerous.palletsprojects.com/en/stable/timed/
payload = serializer.loads(token, max_age=ttl_seconds, salt="approval-token")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| In-memory workflow dict keyed by `run_id` | LangGraph checkpointing with durable `thread_id` | LangGraph 1.1 docs current as of 2026-03-31 | Restart-safe resume is a built-in path, not a custom subsystem. |
| Resume by calling custom Python class state | Resume by re-invoking graph with `Command(resume=...)` and same thread | LangGraph interrupt docs current as of 2026-03-31 | Approval handling becomes explicit and testable. |
| Generic 500s from unhandled exceptions | `HTTPException` or custom handlers for domain errors | FastAPI current docs | Approval failures become stable API contracts. |

**Deprecated/outdated:**
- Process-local pause state in `app.state` for approval workflows: outdated for any restart-safe workflow.
- Approval URLs based on raw `run_id:decision` strings: incompatible with the signed-token contract already present in the repo.

## Open Questions

1. **Should Phase 1 fully replace `app/graph/workflow.py` with a real LangGraph graph, or introduce an adapter layer first?**
   - What we know: The spec and roadmap both call for LangGraph durability now.
   - What's unclear: Whether the planner wants a direct rewrite in one plan or a compatibility layer around existing workflow methods.
   - Recommendation: Plan for a direct graph implementation under `app/graph/` and keep any adapter minimal and temporary.

2. **Will tests use live Postgres in this phase or only SQLite plus targeted integration coverage?**
   - What we know: The project target is Postgres, but current tests are SQLite-heavy.
   - What's unclear: Whether the planner wants Docker-backed Postgres test commands in Phase 1 or to defer that to operational readiness.
   - Recommendation: Include at least one Postgres-backed persistence test path in Phase 1 if feasible; otherwise call out the remaining risk explicitly.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.2` |
| Config file | [pyproject.toml](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml) |
| Quick run command | `pytest tests/api/test_routes.py tests/services/test_persistence.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RUNT-01 | Trigger a run, recreate app/runtime, then approve same persisted run successfully | integration | `pytest tests/api/test_durable_runs.py::test_approval_survives_app_restart -q` | ❌ Wave 0 |
| RUNT-02 | Persist run row, recommendation rows, approval event, and transition trail for a run | integration | `pytest tests/services/test_run_repository.py::test_run_audit_records_persist -q` | ❌ Wave 0 |
| RUNT-03 | Invalid, expired, stale, and duplicate approvals return explicit non-500 responses | API | `pytest tests/api/test_approval_errors.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/api/test_routes.py tests/services/test_persistence.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green plus the new restart-safe approval tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/test_durable_runs.py` — restart-safe trigger/approval flow for RUNT-01
- [ ] `tests/api/test_approval_errors.py` — invalid, expired, stale, duplicate approval cases for RUNT-03
- [ ] `tests/services/test_run_repository.py` — durable run, recommendation, approval, transition persistence for RUNT-02
- [ ] Expand [tests/conftest.py](/Users/nickbohm/Desktop/Tinkering/investor/tests/conftest.py) with DB-session fixtures and app recreation helpers for persistence tests

## Sources

### Primary (HIGH confidence)
- [Investor design spec](/Users/nickbohm/Desktop/Tinkering/investor/docs/specs/2026-03-30-investor-design.md) - product-mandated architecture, durability model, and data model
- [Roadmap](/Users/nickbohm/Desktop/Tinkering/investor/.planning/ROADMAP.md) - Phase 1 success criteria and plan boundaries
- https://docs.langchain.com/oss/python/langgraph/persistence - threads, checkpoints, and why persistence is required
- https://docs.langchain.com/oss/python/langgraph/interrupts - `interrupt()`, `Command(resume=...)`, same-thread resume semantics, approval patterns
- https://docs.langchain.com/oss/python/langgraph/durable-execution - durable execution guidance and idempotency requirement
- https://pypi.org/project/langgraph-checkpoint-postgres/ - official Postgres saver usage and setup requirements
- https://docs.sqlalchemy.org/en/20/orm/session_basics.html - session factory and transaction-scope patterns
- https://fastapi.tiangolo.com/tutorial/handling-errors/ - standard 4xx exception mapping and custom handlers
- https://itsdangerous.palletsprojects.com/en/stable/timed/ - timed signature expiry behavior
- PyPI JSON metadata for `fastapi`, `sqlalchemy`, `alembic`, `psycopg`, `langgraph`, `langgraph-checkpoint-postgres`, `pydantic-settings`, `pytest`, `itsdangerous` - current version and publish-date verification

### Secondary (MEDIUM confidence)
- [Codebase concerns](/Users/nickbohm/Desktop/Tinkering/investor/.planning/codebase/CONCERNS.md) - current implementation gaps aligned with Phase 1
- [Testing map](/Users/nickbohm/Desktop/Tinkering/investor/.planning/codebase/TESTING.md) - existing test coverage and missing behaviors

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - matches local spec direction and official package/docs verification
- Architecture: HIGH - local product docs and official LangGraph/FastAPI/SQLAlchemy docs are aligned
- Pitfalls: HIGH - directly supported by current code gaps plus official interrupt/durable-execution semantics

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
