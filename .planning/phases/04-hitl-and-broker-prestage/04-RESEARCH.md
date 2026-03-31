# Phase 4: HITL And Broker Prestage - Research

**Researched:** 2026-03-31
**Domain:** durable human-in-the-loop workflow resume and safe Alpaca broker prestage
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HITL-01 | Approved runs resume the same persisted workflow instance instead of creating a new one | LangGraph `interrupt()` + durable checkpointer + stable `thread_id` resume pattern |
| HITL-02 | Rejected runs finalize safely without creating broker artifacts | Explicit approval state machine with reject terminal state and no broker side effects on reject path |
| BRKR-01 | Approved recommendations are converted into pre-staged Alpaca order proposals or draft orders for final confirmation | App-owned draft-order artifact service with deterministic sizing and Alpaca-compatible payloads |
| BRKR-02 | Broker prestage logic verifies buying power, tradability, supported order shape, and environment mode before creating the artifact | Alpaca `/v2/account`, `/v2/assets`, documented order constraints, and explicit paper/live mode validation |
| BRKR-03 | Broker artifacts are traceable to the originating run and recommendation set | Persist broker artifact records keyed by `run_id`, recommendation ids, mode, and deterministic `client_order_id` |
</phase_requirements>

## Summary

Phase 4 should be planned as two tightly-coupled but distinct systems: a durable approval state machine and an app-owned broker prestage layer. The approval path must resume the exact persisted workflow thread using the same `thread_id`, record the decision once, and treat duplicate or stale approval attempts as safe no-ops or explicit user errors. This is the core requirement behind `HITL-01` and `HITL-02`.

The broker side should not assume Alpaca provides a broker-side "draft order" savepoint. Alpaca's official Trading API docs document account, assets, and order-placement endpoints, plus paper/live environments, but I did not find an official draft-order endpoint. The safe v1 pattern is to persist an internal broker artifact that is Alpaca-ready, policy-checked, and traceable, while deferring any actual order submission to a later explicit confirmation step.

This phase also depends heavily on assumptions from earlier phases. The current repo still uses an in-memory workflow store in [app/api/routes.py](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py) and a plain Python workflow in [app/graph/workflow.py](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py). Planning for Phase 4 should therefore assume Phase 1 has already delivered durable workflow persistence and explicit run/recommendation records. If that foundation is not in place, the plan needs a Wave 0 prerequisite instead of trying to solve durability inside Phase 4.

**Primary recommendation:** Use LangGraph interrupt/resume with Postgres checkpointing for approval, and persist app-owned Alpaca-ready draft artifacts with deterministic `client_order_id` values instead of treating Alpaca as a draft-order store.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `langgraph` | 1.1.3 | Durable workflow graph with `interrupt()`/resume | Official LangGraph pattern for HITL pause/resume on the same thread |
| `langgraph-checkpoint-postgres` | 3.0.5 | Postgres-backed checkpoint persistence | Official LangGraph Postgres checkpointer integration for durable state |
| `psycopg[binary]` | 3.3.3 | Postgres driver for LangGraph/SQLAlchemy runtime | Current standard psycopg3 path for Python Postgres clients |
| `sqlalchemy` | 2.0.48 | Application-owned broker artifact and audit persistence | Already used in repo; standard ORM for explicit state machine records |
| `fastapi` | 0.135.2 | Approval callback and operational endpoints | Already used; keeps approval and broker flows testable and explicit |

Verified against PyPI on 2026-03-31:
- `langgraph` 1.1.3, uploaded 2026-03-18
- `langgraph-checkpoint-postgres` 3.0.5, uploaded 2026-03-18
- `psycopg` 3.3.3, uploaded 2026-02-18
- `sqlalchemy` 2.0.48, uploaded 2026-03-02
- `fastapi` 0.135.2, uploaded 2026-03-23

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | 0.28.1 | Alpaca HTTP adapter | Use for `/v2/account`, `/v2/assets`, and eventual order APIs |
| `itsdangerous` | 2.2.0 | Signed approval tokens | Keep existing token model instead of inventing a custom format |
| `pydantic-settings` | 2.13.1 | Explicit paper/live env selection and key validation | Use for broker mode, URLs, and fail-fast config |
| `alembic` | 1.18.4 | Schema migrations for broker artifacts and approval state | Use for new broker artifact tables and indexes |
| `pytest` | 9.0.2 | Integration and state-machine tests | Existing test framework; phase should extend it rather than add another |

Verified against PyPI on 2026-03-31:
- `httpx` 0.28.1, uploaded 2024-12-06
- `itsdangerous` 2.2.0, uploaded 2024-04-16
- `pydantic-settings` 2.13.1, uploaded 2026-02-19
- `alembic` 1.18.4, uploaded 2026-02-10
- `pytest` 9.0.2, uploaded 2025-12-06

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `langgraph-checkpoint-postgres` | custom SQLAlchemy checkpoint tables | Worse fit; reimplements durable resume behavior that LangGraph already provides |
| app-owned draft artifact | direct Alpaca order submission in paper mode | Useful only for later explicit confirmation flows; too risky as the default interpretation of "prestage" |
| deterministic `client_order_id` | broker artifact lookup by `run_id` only | Weaker dedupe and weaker traceability if actual order placement is added later |

**Installation:**
```bash
pip install langgraph langgraph-checkpoint-postgres "psycopg[binary]"
```

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── api/                 # approval callback and broker review endpoints
├── graph/               # LangGraph compile/invoke/resume logic
├── services/
│   ├── approvals.py     # state-machine guards and idempotent decision handling
│   ├── broker_policy.py # buying power, mode, asset, and order-shape checks
│   ├── broker_prestage.py
│   └── tokens.py
├── repositories/        # run, recommendation, approval event, broker artifact persistence
├── tools/
│   └── alpaca.py        # typed Alpaca adapter
└── schemas/             # broker artifact, order proposal, and approval DTOs
```

### Pattern 1: Resume The Same Workflow Thread
**What:** Persist the LangGraph checkpoint and store the `thread_id` on the run record. Approval callback loads the run by token `run_id`, verifies the run is still awaiting review, and resumes the graph with the same `thread_id`.
**When to use:** Every approval or rejection path.
**Example:**
```python
from langgraph.types import Command

def resume_run(graph, run_record, decision: str):
    config = {"configurable": {"thread_id": run_record.thread_id}}
    return graph.invoke(Command(resume={"decision": decision}), config=config)
```
Source: LangGraph interrupts docs, https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

### Pattern 2: Separate Approval Decision From Broker Side Effects
**What:** Approval route records a single decision event, transitions the run to `resuming`, then broker prestage happens in a later workflow node or service after state validation.
**When to use:** All approve paths; especially important because LangGraph resumes a node from the beginning after `interrupt()`.
**Example:**
```python
def handle_approval(run, decision, repo):
    repo.record_approval_once(run.run_id, decision)
    if decision == "reject":
        repo.transition(run.run_id, "awaiting_review", "rejected")
        return {"status": "rejected"}
    repo.transition(run.run_id, "awaiting_review", "resuming")
    return {"status": "resuming"}
```
Source: LangGraph interrupts docs, https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

### Pattern 3: Persist App-Owned Broker Artifacts
**What:** Create a `broker_artifacts` table that stores the proposed order payload, broker mode, validation snapshot, and deterministic ids linking back to run and recommendations.
**When to use:** On approved runs after policy checks pass.
**Example:**
```python
artifact = {
    "run_id": run_id,
    "recommendation_id": recommendation_id,
    "broker_mode": mode,
    "client_order_id": client_order_id,
    "payload": order_payload,
    "status": "draft_ready",
}
```
Source: repo requirements + Alpaca order docs, https://docs.alpaca.markets/docs/orders-at-alpaca

### Pattern 4: Broker Policy Is Deterministic And Pre-Submission
**What:** Fetch account state and asset metadata first, then enforce mode, buying power, tradability, and order-shape rules before creating any broker artifact.
**When to use:** Before every prestage attempt.
**Example:**
```python
def validate_prestage(account, asset, order):
    if account["trading_blocked"]:
        raise BrokerPolicyError("account is trading blocked")
    if not asset["tradable"]:
        raise BrokerPolicyError("asset is not tradable")
    if order["type"] == "market" and order.get("notional") and not asset["fractionable"]:
        raise BrokerPolicyError("notional sizing requires fractionable asset")
```
Source: Alpaca account/assets/orders docs, https://docs.alpaca.markets/docs/working-with-account, https://docs.alpaca.markets/docs/working-with-assets, https://docs.alpaca.markets/docs/orders-at-alpaca

### Anti-Patterns to Avoid
- **Broker calls inside the approval route:** The route should decide and resume, not own external side effects.
- **Using `run_id` alone as dedupe:** Store `thread_id`, approval event identity, and deterministic `client_order_id`.
- **Putting side effects before `interrupt()`:** LangGraph re-runs node code before the interrupt on resume.
- **Treating paper and live as a boolean toggle with shared credentials:** Use explicit mode enum plus mode-specific base URL and key validation.
- **Assuming Alpaca has broker-side drafts:** Design app-owned prestage artifacts unless a future phase adds explicit submission.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Durable HITL resume | custom pause/resume state store | LangGraph `interrupt()` + Postgres checkpointer | This is the platform's built-in durability feature |
| Approval token signing | homegrown HMAC token format | `itsdangerous` signed expiring tokens | Existing library and repo code already cover the signed-token use case |
| Broker eligibility rules | LLM-authored eligibility decisions | deterministic broker policy service | Buying power, tradability, and mode validation must be auditable and testable |
| Draft-order traceability | ad hoc JSON blob on run record | dedicated broker artifact table + `client_order_id` | Supports idempotency, audit history, and future confirmation/submission |
| Asset support inference | guessing from ticker metadata already in research output | Alpaca `/v2/assets` lookup | Tradability/fractionability/order support are broker facts, not research facts |

**Key insight:** The deceptive complexity in this phase is not order-sizing math; it is idempotent workflow resume plus safe separation between approval state and broker side effects.

## Common Pitfalls

### Pitfall 1: Duplicate Approval Creates Duplicate Broker Artifacts
**What goes wrong:** Double-clicks or email retries create multiple prestage artifacts for the same run.
**Why it happens:** Approval event logging and broker artifact creation are not protected by a unique state-machine transition.
**How to avoid:** Enforce one terminal approval decision per run state and generate deterministic `client_order_id` values from stable inputs.
**Warning signs:** Two artifacts for one `run_id`, repeated state transitions, or multiple approve events with the same token fingerprint.

### Pitfall 2: Resume Uses Run ID But Not Thread ID
**What goes wrong:** The app loads a run record but accidentally starts a new workflow instead of resuming the paused one.
**Why it happens:** Planning treats persisted business records as sufficient and forgets LangGraph checkpoint identity.
**How to avoid:** Persist `thread_id` on `runs` and always resume with that exact value.
**Warning signs:** Approval appears to work, but resume skips paused state or repeats pre-approval work from a fresh run.

### Pitfall 3: Code Before `interrupt()` Re-Runs On Resume
**What goes wrong:** Email send, audit insert, or broker policy fetch runs twice after approval.
**Why it happens:** LangGraph restarts the node from the beginning when resuming.
**How to avoid:** Keep side effects after the interrupt in separate nodes or behind idempotent guards.
**Warning signs:** Duplicate logs, duplicate emails, or state transitions that repeat on resume.

### Pitfall 4: Paper And Live Modes Share The Same Path
**What goes wrong:** Paper keys hit live URLs or live keys are accepted in paper-only flows.
**Why it happens:** Mode is treated as documentation instead of runtime validation.
**How to avoid:** Validate mode-specific base URL, credentials, and allowed operations before broker prestage.
**Warning signs:** Missing explicit mode field on artifacts, one config path for both environments, or tests that only cover paper mode.

### Pitfall 5: "Prestage" Quietly Becomes "Submit"
**What goes wrong:** The phase crosses the broker safety boundary by placing orders while claiming to draft them.
**Why it happens:** Official Alpaca order APIs are submission APIs, so an uncareful implementation maps "draft" to `POST /v2/orders`.
**How to avoid:** Treat app persistence as the default draft layer and defer actual submission to a later confirmed action.
**Warning signs:** Prestage service calls order placement endpoints directly, especially on live accounts.

## Code Examples

Verified patterns from official/current sources:

### Pause For Approval And Resume Later
```python
from langgraph.types import interrupt, Command

def approval_node(state):
    decision = interrupt({"run_id": state["run_id"], "kind": "approval"})
    if decision["approved"]:
        return Command(goto="broker_prestage")
    return Command(goto="finalize_rejected")
```
Source: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

### Use A Stable Thread ID With A Durable Checkpointer
```python
config = {"configurable": {"thread_id": run_record.thread_id}}
graph.invoke(input_state, config=config)
graph.invoke(Command(resume={"approved": True}), config=config)
```
Source: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

### Fetch Buying Power Before Prestage
```python
account = alpaca_client.get_account()
if account["trading_blocked"]:
    raise BrokerPolicyError("account blocked")
buying_power = Decimal(account["buying_power"])
```
Source: https://docs.alpaca.markets/docs/working-with-account

### Verify Asset Support Before Building An Order Proposal
```python
asset = alpaca_client.get_asset("NVDA")
if not asset["tradable"]:
    raise BrokerPolicyError("asset not tradable")
if use_fractional_notional and not asset["fractionable"]:
    raise BrokerPolicyError("asset not fractionable")
```
Source: https://docs.alpaca.markets/docs/working-with-assets

## State Of The Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Process-local approval store | Durable LangGraph checkpoint + stable `thread_id` | Current LangGraph docs, verified 2026-03-31 | HITL can survive restart and resume the same run |
| Hand-off blob on workflow state | Persisted broker artifact record with validation snapshot | Current repo roadmap + current Alpaca API constraints | Makes prestage auditable and idempotent |
| "Draft" interpreted as order submission | App-owned draft by default, submission only after later explicit confirmation | Inference from current Alpaca docs, verified 2026-03-31 | Preserves the broker safety boundary |

**Deprecated/outdated:**
- In-memory `workflow_store` in [app/main.py](/Users/nickbohm/Desktop/Tinkering/investor/app/main.py): incompatible with restart-safe approval and Phase 4 requirements.
- Plain Python workflow resume in [app/graph/workflow.py](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py): insufficient once approval must resume the same persisted instance.

## Open Questions

1. **Will Phase 1 actually land LangGraph + Postgres checkpointing before Phase 4 starts?**
   - What we know: The design spec expects it, but the current code does not have it yet.
   - What's unclear: Whether the planner should treat that as already delivered or create a Phase 4 Wave 0 prerequisite check.
   - Recommendation: Gate Plan 04-01 on verifying `thread_id` persistence and durable resume already exist.

2. **Should Phase 4 create only app-local draft artifacts, or also support paper-order submission behind a second explicit confirmation endpoint?**
   - What we know: Requirements say "pre-staged Alpaca order proposals or draft orders for final confirmation."
   - What's unclear: Whether paper-mode submission is wanted now or reserved for later.
   - Recommendation: Plan the default implementation around app-local draft artifacts only; treat any actual Alpaca order submission as opt-in and paper-only if included.

3. **What exact order-shape policy is desired for v1?**
   - What we know: Alpaca supports multiple order types, but fractional trading docs currently emphasize market orders only.
   - What's unclear: Whether v1 should allow only simple long equity buys with market/notional sizing.
   - Recommendation: Plan the narrowest safe policy first: long-only US equities, `buy`, market/notional or qty sizing, no shorts, no options, no complex order classes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` (repo framework; latest PyPI version verified: 9.0.2) |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HITL-01 | approval resumes the same persisted thread/run | integration | `python -m pytest tests/integration/test_hitl_resume.py::test_approval_resumes_same_thread -q` | ❌ Wave 0 |
| HITL-02 | rejection finalizes without broker artifact creation | integration | `python -m pytest tests/integration/test_hitl_resume.py::test_reject_finalizes_without_broker_side_effects -q` | ❌ Wave 0 |
| BRKR-01 | approved recommendations create persisted draft artifacts | integration | `python -m pytest tests/integration/test_broker_prestage.py::test_approved_run_creates_broker_artifacts -q` | ❌ Wave 0 |
| BRKR-02 | buying power, asset support, order shape, and mode rules block invalid prestage | unit + integration | `python -m pytest tests/services/test_broker_policy.py tests/integration/test_broker_prestage.py -q` | ❌ Wave 0 |
| BRKR-03 | broker artifacts are traceable to run and recommendations | integration | `python -m pytest tests/integration/test_broker_prestage.py::test_broker_artifact_links_to_run_and_recommendations -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py -q`
- **Per wave merge:** `python -m pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/integration/test_hitl_resume.py` — durable approve/reject/duplicate/stale coverage for HITL-01 and HITL-02
- [ ] `tests/integration/test_broker_prestage.py` — end-to-end approval-to-artifact coverage for BRKR-01 through BRKR-03
- [ ] `tests/services/test_broker_policy.py` — deterministic policy checks for buying power, asset support, and order shape
- [ ] Shared fixtures for persisted run state, recommendations, and mocked Alpaca account/asset responses

## Sources

### Primary (HIGH confidence)
- LangGraph interrupts docs: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
- LangGraph checkpointer integrations: https://docs.langchain.com/oss/python/integrations/checkpointers/index
- LangGraph durable execution docs: https://docs.langchain.com/oss/python/langgraph/durable-execution
- Alpaca Trading API overview: https://docs.alpaca.markets/docs/trading-api
- Alpaca account docs: https://docs.alpaca.markets/docs/working-with-account
- Alpaca assets docs: https://docs.alpaca.markets/docs/working-with-assets
- Alpaca orders docs: https://docs.alpaca.markets/docs/orders-at-alpaca
- PyPI package metadata:
  - https://pypi.org/pypi/langgraph/json
  - https://pypi.org/pypi/langgraph-checkpoint-postgres/json
  - https://pypi.org/pypi/psycopg/json
  - https://pypi.org/pypi/fastapi/json
  - https://pypi.org/pypi/sqlalchemy/json

### Secondary (MEDIUM confidence)
- Investor design spec: `docs/superpowers/specs/2026-03-30-investor-design.md`
- Current repo implementation:
  - [app/api/routes.py](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py)
  - [app/graph/workflow.py](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py)
  - [app/tools/alpaca.py](/Users/nickbohm/Desktop/Tinkering/investor/app/tools/alpaca.py)
  - [app/db/models.py](/Users/nickbohm/Desktop/Tinkering/investor/app/db/models.py)

### Tertiary (LOW confidence)
- No low-confidence third-party sources were needed.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified against current official LangGraph, Alpaca, and PyPI sources
- Architecture: HIGH - directly aligned with official LangGraph HITL/checkpointer model and repo constraints
- Pitfalls: HIGH - based on current LangGraph resume semantics, Alpaca API behavior, and observed repo gaps

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
