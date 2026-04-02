# Phase 17: Harden Live-Run Approval, Observability, And Replay Operations - Research

**Researched:** 2026-04-02
**Domain:** Live-run operations, replay safety, provider-failure observability, and Quiver research-flow architecture capture
**Confidence:** MEDIUM

## User Constraints

No `*-CONTEXT.md` exists for Phase 17, so there are no phase-specific locked decisions copied from upstream discussion.

Repo and roadmap constraints that still apply:
- Keep the existing Python/FastAPI/Postgres direction.
- Reuse the current route -> workflow engine -> persisted run path instead of inventing a second operator surface.
- Preserve the repo's explicit safety boundary: approval remains separate from broker submission, and live trading must not be silently triggered by replay tooling.
- Keep the architecture capture repo-owned with Excalidraw source plus exported screenshot wired into `README.md`.
- Keep operator-facing runbooks and safety checks grounded in real credentials and delivery paths, not mock-only workflows.

Planning-relevant gaps caused by the missing `CONTEXT.md`:
- No locked decision exists yet for whether Phase 15 live-proof tooling lands before Phase 17 or must be recreated as Wave 0 inside this phase.
- No locked decision exists yet for whether replay should support both evidence-backed `replay` and live-provider `re-drive`, or only one mode in Phase 17.
- No locked decision exists yet for whether the Quiver API diagram should replace `docs/architecture/flow-steps/03-research-agent-quiver-loop.*` or live beside it as a new focused asset.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPS-01 | Operators can distinguish Quiver, LLM, SMTP, approval-link, and broker-side failures from persisted records and logs without code spelunking. | Summary, Standard Stack, Architecture Patterns 1-3, Don't Hand-Roll, Common Pitfalls 1-3, Validation Architecture |
| OPS-02 | A specific live run can be replayed or re-driven with preserved evidence and trace context for debugging and quality review. | Summary, Architecture Patterns 2-4, Runtime State Inventory, Common Pitfalls 4-5, Validation Architecture |
| OPS-03 | Secrets handling, runbooks, and safety checks are sufficient for iterating on live credentials without leaks or silent misrouting. | Standard Stack, Architecture Patterns 1 and 5, Don't Hand-Roll, Common Pitfalls 3 and 6, Validation Architecture |
| ARCH-OPS-04 | The repo contains a readable Excalidraw plus screenshot and README explanation of the real Quiver research flow, specific API calls, and why each call exists. | Summary, Architecture Pattern 5, Code Examples, Common Pitfalls 6-7, Validation Architecture |
</phase_requirements>

## Summary

Phase 17 should be planned as an operational hardening phase on top of the existing persisted-run architecture, not as a platform rewrite. The current repo already has the right execution seam: `/runs/trigger/scheduled` creates the durable run, `WorkflowEngine.start_run()` persists `state_payload`, the approval route records `approval_events`, and broker steps are traceable through `state_transitions` plus `broker_artifacts`. What is missing is the operator-facing evidence layer. Today, live debugging still depends on scattered log lines, raw `state_payload` inspection, and human memory. Planning should therefore add a first-class operation-event ledger and a route-owned replay surface rather than pushing more implicit detail into `runs.state_payload`.

The most important design choice is to separate three concepts that are currently blended together: original run history, evidence-preserving replay, and live-provider re-drive. The original run must remain immutable as the audit record. A replay should create a new run linked by `replay_of_run_id` and reuse persisted evidence plus trace metadata so quality review can reproduce the prior outcome without re-hitting Quiver, SMTP, or broker side effects. A re-drive should also create a new linked run, but it may re-query external providers and must keep email, approval-link, and broker actions disabled by default until explicitly requested. That split is the cleanest way to satisfy the roadmap's "replayable and safe to operate" goal without corrupting the original evidence trail.

There is also a sequencing risk the planner must account for: Phase 17 depends on Phase 16, but the repo does not yet contain Phase 15 live-proof code or Phase 16 research artifacts. In concrete terms, `app/ops/live_proof.py`, `tests/ops/test_live_proof.py`, and the Phase 15 runbook/template are still absent, while `RunRecord.replay_of_run_id` exists but no replay route or service uses it. Plan Phase 17 either after those missing prerequisites land or include a Wave 0 that restores the Phase 15 ops seam before adding replay and observability on top of it.

**Primary recommendation:** Add a first-class `operation_events` persistence surface plus a linked-run replay/re-drive path that reuses the existing routes and workflow engine, and create a separate Quiver-call Excalidraw focused on the four current live endpoints rather than overloading the generic loop diagram.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.3 | Owns the operator-facing HTTP seams for trigger, approval, execute, replay, and probe endpoints | Replay and live-run operations should stay route-owned, just like the current trigger and approval flow |
| SQLAlchemy | 2.0.48 | Persists runs, transitions, approvals, broker artifacts, and the recommended new operation-event ledger | The repo already uses SQLAlchemy as the single durable truth surface |
| pydantic-settings | 2.13.1 | Loads `.env` and `INVESTOR_*` runtime config for live-safe ops commands and startup checks | This phase is heavily about config hygiene, redaction, and safety gating |
| httpx | 0.28.1 | Drives Quiver, OpenAI-compatible LLM checks, approval probes, and any route-backed ops CLI calls | The repo already standardizes external HTTP around `httpx` |
| pytest | 9.0.2 | Provides the existing repo test framework for route, integration, and docs drift coverage | Phase 17 needs regression coverage around replay, event logging, and docs assets |
| Python `logging` | stdlib (3.12) | Adds contextual log fields such as `run_id`, `stage`, `provider`, and `event_id` | Official Python logging already supports structured/contextual patterns via adapters, filters, and cookbook patterns without adding another logging framework mid-project |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Uvicorn | 0.42.0 | Serves the real app process for approval probes and operator routes | Use for all live ops and replay HTTP boundaries |
| psycopg | 3.3.3 | Connects to Postgres for persisted run inspection and replay lineage writes | Use wherever Phase 17 needs DB-backed operational truth |
| Python `smtplib` / `email` | stdlib (3.12) | Maintains the repo's real SMTP delivery seam | Keep existing SMTP behavior, but log/send safety around it more clearly |
| Excalidraw | repo-owned asset format | Owns the editable Quiver research-flow diagram source | Use for the new endpoint-specific diagram and exported screenshot |
| Docker Compose | repo runtime | Keeps the live ops workflow on the documented runtime path | Use for preflight, logs, and operator proof steps instead of one-off scripts |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stdlib logging + contextual extras + persisted operation events | OpenTelemetry collector stack | More powerful for distributed systems, but overkill for this single-operator local-first repo and it would add operational infrastructure before basic run taxonomy exists |
| Linked replay runs using `replay_of_run_id` | Mutating the original run row in place | Faster to hack, but destroys auditability and makes debugging impossible once live credentials are involved |
| Route-backed replay and probe commands | Direct workflow-engine or repository calls from ad hoc scripts | Bypasses auth, logging, and safety checks, which are the core of this phase |
| A new focused Quiver-call diagram asset | Stuffing endpoint labels into the existing generic loop screenshot | The current Step 3 asset explains the loop shape, not the specific API calls and why each exists |

**Installation / verification commands:**
```bash
pip install -e .
PYTHONPATH=. pytest -q
```

**Version verification:** Verified against PyPI JSON and official package indexes on 2026-04-02.

| Package | Latest | Published |
|---------|--------|-----------|
| FastAPI | 0.135.3 | 2026-04-01 |
| SQLAlchemy | 2.0.48 | 2026-03-02 |
| pydantic-settings | 2.13.1 | 2026-02-19 |
| httpx | 0.28.1 | 2024-12-06 |
| pytest | 9.0.2 | 2025-12-06 |
| Uvicorn | 0.42.0 | 2026-03-16 |
| Jinja2 | 3.1.6 | 2025-03-05 |
| psycopg | 3.3.3 | 2026-02-18 |

## Architecture Patterns

### Recommended Project Structure

```text
app/
├── api/routes.py                  # existing trigger/approval/execute routes plus replay/probe surfaces
├── ops/live_run_ops.py            # repo-owned CLI for inspect, replay, re-drive, and preflight-safe summaries
├── repositories/runs.py           # existing run access plus linked-run lineage helpers
├── repositories/operation_events.py  # new provider/stage event ledger
├── services/operation_events.py   # typed event writes and redaction helpers
├── services/replay.py             # replay and re-drive orchestration over existing runtime seams
├── workflows/engine.py            # start_run + advance_run stay authoritative
└── tools/quiver.py                # real Quiver endpoint wrappers used by live and replay flows
docs/architecture/
├── flow-steps/03-research-agent-quiver-loop.excalidraw   # keep existing generic loop
├── quiver-research-flow.excalidraw                       # new focused endpoint-level diagram
└── quiver-research-flow.png                              # exported screenshot used by README
tests/
├── ops/                         # CLI, safety, and docs drift coverage
├── integration/                 # replay and provider-failure lifecycle coverage
└── services/                    # event-ledger, replay-policy, and redaction units
```

### Pattern 1: Persist Operation Events Separately From `runs.state_payload`

**What:** Add a first-class operation-event ledger keyed by `run_id` for provider-stage outcomes such as `quiver.fetch`, `llm.complete`, `smtp.send`, `approval.verify`, `approval.apply`, `broker.prestage`, and `broker.submit`.

**When to use:** Always for live provider interactions and replay/re-drive bookkeeping.

**Example:**
```python
# Source: project adaptation over app/workflows/engine.py + app/services/mail_provider.py
event = operation_events.record(
    run_id=run_id,
    stage="smtp.send",
    provider="smtp",
    outcome="failure",
    error_code=exc.__class__.__name__,
    detail=str(exc),
    trace_id=trace_id,
)
logger.info(
    "operation_event run_id=%s stage=%s provider=%s outcome=%s event_id=%s",
    run_id,
    event.stage,
    event.provider,
    event.outcome,
    event.id,
)
```

### Pattern 2: Replay And Re-Drive Must Create New Linked Runs

**What:** Use `RunRecord.replay_of_run_id` as lineage for both replay and re-drive. Never mutate the original run into a replayed state.

**When to use:** For all operator-triggered debugging, quality review, or provider re-check flows.

**Example:**
```python
# Source: project adaptation over app/db/models.py and app/services/run_service.py
replay_run = run_service.create_pending_run(
    run_id=new_run_id,
    status="triggered",
    current_step="research",
    trigger_source="replay",
)
repository.attach_replay_lineage(
    replay_run,
    replay_of_run_id=original_run.run_id,
)
repository.update_state_payload(
    replay_run,
    {
        "replay_mode": "evidence_only",
        "source_run_id": original_run.run_id,
        "evidence_bundles": original_run.state_payload["evidence_bundles"],
        "research_trace": original_run.state_payload["research_trace"],
    },
)
```

### Pattern 3: Keep Replay Route-Owned And Side-Effect Guarded

**What:** The same operator-safety contract used for scheduled trigger and execute should own replay. Replay commands should go through a route or a route-backed CLI that can enforce auth, mode flags, and side-effect suppression.

**When to use:** For `replay`, `re-drive`, and approval-boundary probe operations.

**Example:**
```python
# Source: repo pattern in app/api/routes.py
if replay_trigger != runtime.settings.scheduled_trigger_token:
    raise HTTPException(status_code=401, detail="Invalid replay trigger token")

result = runtime.replay_service.start(
    source_run_id=run_id,
    mode="evidence_only",
    allow_email=False,
    allow_broker=False,
)
```

### Pattern 4: Use Contextual Logging, Not Free-Form Strings

**What:** Keep using the stdlib logger, but inject stable context fields (`run_id`, `provider`, `stage`, `event_id`, `replay_of_run_id`) through a shared adapter or filter so logs line up with persisted event rows.

**When to use:** For all live-run, replay, and safety checks.

**Example:**
```python
# Source: Python logging cookbook + project logging style
logger = logging.LoggerAdapter(
    logging.getLogger(__name__),
    {
        "run_id": run_id,
        "provider": "quiver",
        "stage": "quiver.fetch",
    },
)
logger.info("operation started")
logger.exception("operation failed")
```

### Pattern 5: Create A Dedicated Quiver Research-Flow Diagram

**What:** Add a new Excalidraw focused on the current real Quiver calls and why they exist: `/beta/live/congresstrading`, `/beta/live/insiders`, `/beta/live/govcontracts`, and `/beta/live/lobbying`, plus how the workflow turns them into evidence bundles, shortlist seeds, tool-driven follow-ups, and final recommendations.

**When to use:** For `ARCH-OPS-04`.

**Example:**
```text
/beta/live/congresstrading -> broad unusual legislative trade signal
/beta/live/insiders -> ticker-specific corporate insider confirmation
/beta/live/govcontracts -> contract-backed demand / revenue context
/beta/live/lobbying -> policy/regulatory interest context
```

### Anti-Patterns to Avoid

- **Stuffing provider failures into one generic `Scheduled trigger failed` error:** It hides the exact broken boundary and fails `OPS-01`.
- **Replaying by directly calling `workflow_engine.start_run()` from a shell script:** It bypasses route auth, logging, and future safety flags.
- **Reusing the original run id for replay:** It corrupts lineage and makes postmortems ambiguous.
- **Allowing replay to resend live email or broker artifacts by default:** Safe replay should be side-effect off unless explicitly enabled.
- **Documenting Quiver flow only in prose:** The roadmap explicitly requires a repo-owned Excalidraw plus screenshot.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider observability | Ad hoc `print()` debugging and loose JSON blobs in `state_payload` | A typed `operation_events` table plus contextual stdlib logging | Operators need queryable, stage-specific failure history tied to the run |
| Replay lineage | In-place row rewrites or manual SQL updates | New linked runs via `replay_of_run_id` | Original evidence must remain intact for audit and comparison |
| Secret redaction | Scattered string replacement at every log site | One shared redaction helper over existing settings/CLI output paths | Centralized masking prevents partial leaks and drift |
| Probe/replay commands | Shell scripts that call internal Python services directly | Repo-owned Python CLI backed by existing routes and session factories | The phase is about safe operator surfaces, not hidden shortcuts |
| Quiver architecture docs | Hand-edited PNGs or README-only bullet lists | Excalidraw source + exported screenshot + docs drift test | The diagram must stay editable and verifiable as the code evolves |

**Key insight:** The hard part of Phase 17 is not adding more logs. It is establishing one durable, queryable operational truth surface that matches the HTTP/runtime boundaries the operator actually uses.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `runs` already persist `state_payload`, `approval_status`, `current_step`, and `replay_of_run_id`; `approval_events`, `state_transitions`, and `broker_artifacts` already exist. No `operation_events`-style provider ledger exists yet. | Code edit plus DB migration: add a first-class operation-event table. Code edit: add replay lineage writers/readers. No mandatory migration for existing rows if null-safe readers are used. |
| Live service config | SMTP account, OpenAI-compatible endpoint/model, Quiver API key/base URL, and `INVESTOR_EXTERNAL_BASE_URL` live outside git. Phase 15 runbook and CLI are still missing, so there is no repo-owned live-ops surface yet. | Code edit plus docs: restore/create the repo-owned live-proof CLI and runbook before layering Phase 17 replay and observability on top. |
| OS-registered state | Docker Compose runtime and app-container scheduler are the current operator path. No repo evidence shows additional launchd/systemd/pm2 registrations tied to replay or live proof. | None verified beyond current Docker runtime. Keep Phase 17 route/CLI assets container-friendly and avoid host-only assumptions. |
| Secrets/env vars | `INVESTOR_*` env contract lives in `app/config.py` and `.env.example`; SMTP password, Quiver key, OpenAI key, trigger tokens, and app secret are sensitive. Existing logs already include recipient email and route outcomes; no centralized redaction layer exists for future richer event payloads. | Code edit: add redaction/masking for ops CLI output and persisted operation-event details. Keep secret names unchanged unless a later phase explicitly migrates them. |
| Build artifacts | Existing docs screenshots under `docs/architecture/` are exported assets that can drift from the `.excalidraw` source. No dedicated Quiver-call screenshot asset exists yet. | Code edit/docs: add new `.excalidraw` plus PNG export and README linkage; update docs drift tests so screenshot/source pairs stay aligned. |

## Common Pitfalls

### Pitfall 1: Provider Failures Collapse Into One Generic Run Failure

**What goes wrong:** Quiver 401s, LLM tool-call failures, SMTP auth issues, approval-link problems, and broker-side rejects all surface as one opaque run failure.

**Why it happens:** The current repo logs some boundary-specific lines, but the durable DB model does not persist a provider-stage taxonomy.

**How to avoid:** Add a typed operation-event ledger with stable fields such as `stage`, `provider`, `outcome`, `error_code`, `http_status`, and `detail`.

**Warning signs:** Operators must read Python stack traces or inspect code to tell whether the run failed before or after memo delivery.

### Pitfall 2: Logs And DB Rows Cannot Be Correlated Reliably

**What goes wrong:** The run has persisted state, but the logs cannot be joined to a specific provider attempt or replay lineage.

**Why it happens:** Current logging includes `schedule_key` and `run_id` for some paths, but not a consistent event id or replay lineage across all providers.

**How to avoid:** Add contextual logging fields that mirror persisted event ids and `replay_of_run_id`.

**Warning signs:** Two runs on the same day produce similar log lines and the operator cannot tell which failure belongs to which run.

### Pitfall 3: Secrets Leak Through Preflight Or Replay Tooling

**What goes wrong:** Ops helpers print full URLs with embedded tokens, SMTP usernames/password hints, or raw provider payloads into terminal history, logs, or phase artifacts.

**Why it happens:** Operators often add debugging output quickly once live credentials are involved.

**How to avoid:** Centralize redaction and limit persisted event details to masked hostnames, status codes, and safe summaries.

**Warning signs:** A proof artifact or log line contains bearer tokens, SMTP passwords, or signed approval tokens.

### Pitfall 4: Replay Overwrites The Original Audit Record

**What goes wrong:** A replay mutates the original run's `state_payload`, transitions, or approval fields, so the real historical record disappears.

**Why it happens:** Reusing the original row looks simpler than creating a lineage-linked run.

**How to avoid:** Treat replay as a new run every time, and link it to the source run with `replay_of_run_id`.

**Warning signs:** The same `run_id` appears to have multiple contradictory final states or evidence snapshots.

### Pitfall 5: Replay Accidentally Re-Sends Email Or Broker Actions

**What goes wrong:** A debug replay fires SMTP, approval links, or broker side effects unexpectedly.

**Why it happens:** The existing engine assumes normal production behavior unless the caller explicitly suppresses side effects.

**How to avoid:** Make `allow_email=False`, `allow_approval_links=False`, and `allow_broker=False` the replay defaults; require explicit flags to override.

**Warning signs:** A replay creates new approval links or broker artifacts before the operator asked for them.

### Pitfall 6: The New Diagram Drifts From The Real Quiver Client

**What goes wrong:** The README screenshot explains endpoints or purposes that no longer match `app/tools/quiver.py` or Quiver's published schema.

**Why it happens:** Architecture screenshots are easy to update manually without checking code.

**How to avoid:** Anchor the diagram to the exact four methods in `app/tools/quiver.py` and the current Quiver schema, then add docs drift tests.

**Warning signs:** The diagram names endpoints that do not exist in `app/tools/quiver.py` or omits one of the current live calls.

### Pitfall 7: Planning Assumes Phase 15/16 Ops Assets Already Exist

**What goes wrong:** The plan starts from replay/observability features that depend on a live-proof CLI or evaluation fixtures that are not actually present.

**Why it happens:** The roadmap has moved ahead faster than the checked-in implementation.

**How to avoid:** Make the missing Phase 15 live-proof surface and any Phase 16 eval artifacts explicit Wave 0 prerequisites if they remain absent at execution time.

**Warning signs:** The plan references `app/ops/live_proof.py`, `tests/ops/test_live_proof.py`, or Phase 16 artifacts that do not exist in the worktree.

## Code Examples

Verified patterns from repo and official sources:

### Contextual Provider Logging
```python
# Source: https://docs.python.org/3/howto/logging-cookbook.html
import logging

base_logger = logging.getLogger("investor.ops")
logger = logging.LoggerAdapter(
    base_logger,
    {"run_id": run_id, "provider": "smtp", "stage": "smtp.send"},
)

logger.info("operation started")
```

### Current Quiver Call Surface
```python
# Source: /Users/nickbohm/Desktop/Tinkering/investor/app/tools/quiver.py
def get_live_congress_trading(self, ticker: str | None = None):
    return self._get("/beta/live/congresstrading", ticker=ticker)

def get_live_insider_trading(self, ticker: str | None = None):
    return self._get("/beta/live/insiders", ticker=ticker)

def get_live_government_contracts(self, ticker: str | None = None):
    return self._get("/beta/live/govcontracts", ticker=ticker)

def get_live_lobbying(self, ticker: str | None = None):
    return self._get("/beta/live/lobbying", ticker=ticker)
```

### Linked Replay Run Creation
```python
# Source: project adaptation over /Users/nickbohm/Desktop/Tinkering/investor/app/db/models.py
replay_run = RunRecord(
    run_id=f"run-{uuid4().hex[:8]}",
    status="triggered",
    current_step="research",
    trigger_source="replay",
    replay_of_run_id=source_run.run_id,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic "run failed" or route-only logs | Stage- and provider-specific operation-event taxonomy tied to the run | Current best practice for app-owned workflow ops; adopt in Phase 17 | Operators can debug from persisted evidence instead of stack traces |
| Re-running a workflow by hand or mutating prior state | New lineage-linked replay/re-drive runs | Already supported conceptually by `replay_of_run_id`; not yet implemented in repo | Preserves auditability and enables safe comparison |
| One generic Quiver-loop diagram | A focused endpoint-level Quiver flow diagram plus exported screenshot | Needed now that the repo has concrete Quiver methods and live-proof phases | README explains exactly what each API call contributes |

**Deprecated/outdated:**
- Free-form replay by shell or notebook: too risky once SMTP, approval links, and broker paths use live credentials.
- Screenshot-only architecture docs: the roadmap now requires the Excalidraw source to remain the editable truth.

## Open Questions

1. **Should Phase 17 implement both `replay` and `re-drive`, or only `replay` first?**
   - What we know: The roadmap says "replayed or re-driven", and the repo already stores enough evidence to support an evidence-only replay.
   - What's unclear: Whether the first execution plan should also re-hit Quiver/LLM live providers.
   - Recommendation: Plan `replay` first as the safe default, then add `re-drive` behind stricter flags if Phase 16 evaluation work needs it immediately.

2. **Should operation events remain in Postgres only, or also be emitted as structured JSON logs?**
   - What we know: The repo already relies on Docker/app logs for operator observability, and Postgres is the durable truth.
   - What's unclear: Whether Phase 17 needs machine-readable JSON log output in addition to DB rows.
   - Recommendation: Persist the event ledger first and keep log formatting minimal but contextual; only adopt full JSON log formatting if operators actually need external log ingestion.

3. **Should the Quiver-call diagram replace the existing Step 3 asset or live beside it?**
   - What we know: The current Step 3 diagram explains the loop shape well but not the exact API calls or reasons.
   - What's unclear: Whether replacing it would make the README less approachable.
   - Recommendation: Keep Step 3 as the generic loop diagram and add a separate `docs/architecture/quiver-research-flow.excalidraw` focused on endpoint purpose and call flow.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none |
| Quick run command | `PYTHONPATH=. pytest tests/ops/test_live_run_observability.py tests/services/test_operation_events.py tests/integration/test_replay_ops.py tests/ops/test_operational_docs.py -q` |
| Full suite command | `PYTHONPATH=. pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPS-01 | Provider-stage failures are distinguishable from DB rows and logs for Quiver, LLM, SMTP, approval, and broker paths | integration + ops | `PYTHONPATH=. pytest tests/ops/test_live_run_observability.py tests/services/test_operation_events.py -q` | ❌ Wave 0 |
| OPS-02 | Replay creates a linked run with preserved evidence/trace, while re-drive stays side-effect gated | integration | `PYTHONPATH=. pytest tests/integration/test_replay_ops.py -q` | ❌ Wave 0 |
| OPS-03 | Preflight, redaction, host safety checks, and docs prevent secret leaks and silent misrouting | ops + docs | `PYTHONPATH=. pytest tests/ops/test_live_run_safety.py tests/ops/test_operational_docs.py -q` | ❌ Wave 0 / ✅ existing docs file |
| ARCH-OPS-04 | Excalidraw source, exported screenshot, and README explanation stay aligned to real Quiver calls | docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=. pytest tests/ops/test_live_run_observability.py tests/services/test_operation_events.py tests/integration/test_replay_ops.py tests/ops/test_operational_docs.py -q`
- **Per wave merge:** `PYTHONPATH=. pytest -q`
- **Phase gate:** Full suite green plus one manual replay/re-drive runbook walkthrough before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/services/test_operation_events.py` — covers typed provider/stage event persistence and redaction-safe detail storage
- [ ] `tests/ops/test_live_run_observability.py` — covers inspect output, provider failure taxonomy, and log/DB correlation fields
- [ ] `tests/integration/test_replay_ops.py` — covers linked replay runs, preserved evidence/trace payloads, and side-effect suppression defaults
- [ ] `tests/ops/test_live_run_safety.py` — covers probe host checks, masked secrets, and replay/re-drive safety flags
- [ ] `app/ops/live_run_ops.py` or equivalent repo-owned CLI — current repo has no Phase 15 live-proof CLI to extend

## Sources

### Primary (HIGH confidence)

- Project code: [app/api/routes.py](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py), [app/workflows/engine.py](/Users/nickbohm/Desktop/Tinkering/investor/app/workflows/engine.py), [app/graph/workflow.py](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py), [app/tools/quiver.py](/Users/nickbohm/Desktop/Tinkering/investor/app/tools/quiver.py), [app/db/models.py](/Users/nickbohm/Desktop/Tinkering/investor/app/db/models.py), [README.md](/Users/nickbohm/Desktop/Tinkering/investor/README.md) - verified the current runtime seam, replay gap, logging surface, and existing diagram assets
- Quiver API docs: `https://api.quiverquant.com/docs` and `https://api.quiverquant.com/docs/schema.json` - verified current published paths including `/beta/live/congresstrading`, `/beta/live/insiders`, `/beta/live/govcontracts`, and `/beta/live/lobbying`
- Quiver official Python API README: `https://github.com/Quiver-Quantitative/python-api/blob/master/README.md` - verified Quiver's official dataset naming and intended usage surface
- Python logging docs: `https://docs.python.org/3/howto/logging-cookbook.html` and `https://docs.python.org/3/library/logging.html` - verified contextual logging patterns via LoggerAdapter, filters, and structured logging guidance
- Pydantic settings docs: `https://docs.pydantic.dev/latest/concepts/pydantic_settings/` - verified that environment-variable and dotenv support remain first-class patterns for settings-backed runtime config
- PyPI package indexes: `https://pypi.org/pypi/fastapi/json`, `https://pypi.org/pypi/sqlalchemy/json`, `https://pypi.org/pypi/pydantic-settings/json`, `https://pypi.org/pypi/httpx/json`, `https://pypi.org/pypi/pytest/json`, `https://pypi.org/pypi/uvicorn/json`, `https://pypi.org/pypi/Jinja2/json`, `https://pypi.org/pypi/psycopg/json` - verified current package versions and publish dates

### Secondary (MEDIUM confidence)

- Phase 15 planning artifacts: [15-RESEARCH.md](/Users/nickbohm/Desktop/Tinkering/investor/.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-RESEARCH.md), [15-VALIDATION.md](/Users/nickbohm/Desktop/Tinkering/investor/.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-VALIDATION.md), [15-02-PLAN.md](/Users/nickbohm/Desktop/Tinkering/investor/.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-02-PLAN.md), [15-03-PLAN.md](/Users/nickbohm/Desktop/Tinkering/investor/.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-03-PLAN.md) - useful for sequencing and identifying missing prerequisites, but not yet implemented in code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - package versions were verified from PyPI and the recommended stack aligns with the checked-in repo
- Architecture: MEDIUM - the replay/event-ledger recommendations are strongly grounded in current repo seams, but Phase 15/16 prerequisites are still missing
- Pitfalls: MEDIUM - several pitfalls are directly visible in the current codebase, while others are forward-looking operational risks inferred from the roadmap

**Research date:** 2026-04-02
**Valid until:** 2026-05-02
