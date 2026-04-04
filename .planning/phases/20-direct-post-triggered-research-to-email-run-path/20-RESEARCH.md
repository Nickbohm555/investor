# Phase 20: Direct POST-triggered research-to-email run path - Research

**Researched:** 2026-04-03
**Domain:** FastAPI manual trigger path, live-ops proof tooling, research-to-email workflow reuse
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Trigger surface
- **D-01:** Phase 20 should center on a direct manual POST-triggered run, not the cron-owned `/runs/trigger/scheduled` path.
- **D-02:** Planning should prefer reusing the existing `POST /runs/trigger` route and the current runtime/workflow stack unless research finds a concrete blocker.
- **D-03:** Success should be measured from one operator action that starts the run through one delivered email, with no scheduler dependency in the happy path.

### Live proof target
- **D-04:** The immediate product goal is "POST call -> research agent -> email now", not the broader end-to-end approval or broker lifecycle.
- **D-05:** The phase should produce a path that is simple enough to run manually while live env setup is still being stabilized.
- **D-06:** The delivered email itself is the proof artifact that matters for this phase; approval-link clicking is not required.

### Environment assumptions
- **D-07:** The planner should treat missing live env values as first-class blockers for this phase and make them explicit in the operator flow.
- **D-08:** The current live env confusion is not primarily the inbox address. The missing or placeholder values more likely to block a real run are `INVESTOR_QUIVER_BASE_URL`, `INVESTOR_SMTP_HOST`, `INVESTOR_SMTP_PORT`, `INVESTOR_SMTP_USERNAME`, `INVESTOR_SMTP_SECURITY`, and `INVESTOR_EXTERNAL_BASE_URL`.
- **D-09:** `INVESTOR_DAILY_MEMO_TO_EMAIL` may stay equal to `INVESTOR_SMTP_FROM_EMAIL` for the live proof if that is the intended operator inbox.
- **D-10:** For Gmail-backed SMTP, planning should assume `smtp.gmail.com`, port `587`, and `INVESTOR_SMTP_SECURITY=starttls` unless the user chooses a different provider.

### Proof and operator ergonomics
- **D-11:** This phase should reduce operational ambiguity. If a live run cannot proceed, the operator should learn exactly which prerequisite failed instead of discovering it indirectly.
- **D-12:** If `INVESTOR_EXTERNAL_BASE_URL` is not yet publicly usable, the phase should still stay focused on getting the email out, while keeping the rendered host truthful in the delivered memo.

### the agent's Discretion
- Whether the best operator-facing proof path should be a small new live-run helper, an extension of existing live-proof tooling, or a documented direct API invocation flow
- Whether to add a dedicated docs/runbook artifact for the manual POST path or fold the guidance into existing operational docs
- Exact error-surfacing and preflight UX, as long as it clearly identifies which live dependency is blocking a direct run

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Reintroducing cron and scheduled-trigger proof to this narrower live path
- Approval callback verification or replay work
- Broker execution confirmation or live order submission
- Broader operational cleanup beyond what is necessary to get one manual POST-triggered email out
</user_constraints>

## Summary

Phase 20 should not build a new execution path. The repo already has the path the phase wants: [`POST /runs/trigger`](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py), [`WorkflowEngine.start_run(...)`](/Users/nickbohm/Desktop/Tinkering/investor/app/workflows/engine.py), and workflow email delivery in [`CompiledInvestorWorkflow.invoke(...)`](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py). The planning target is to harden and expose that path for live operator use.

The real gap is operational proof, not orchestration. Phase 19’s tooling is centered on scheduled execution and its preflight currently aborts on Quiver/LLM failures before SMTP is even inspected. For Phase 20, the planner should center on a manual POST proof helper or runbook that uses the existing manual route, surfaces readiness failures in operator order, triggers the route once, then inspects persisted run state and delivered email as the proof artifact.

**Primary recommendation:** Extend the existing live-proof surface to support a direct manual `POST /runs/trigger` run, with explicit staged preflight diagnostics and targeted tests/docs, while leaving the runtime and workflow stack unchanged.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | repo installed `0.115.12` / PyPI latest `0.128.8` | HTTP route for manual trigger | Existing API layer already exposes the exact manual entrypoint needed. |
| SQLAlchemy | repo installed `2.0.31` / PyPI latest `2.0.49` | Persist run state before and after invoke | Current run lifecycle and inspection tooling already depend on it. |
| Pydantic Settings | repo installed `2.8.1` / PyPI latest `2.11.0` | `.env`-backed runtime config | Existing startup/readiness flow is built around `BaseSettings` + `env_file`. |
| HTTPX | repo installed `0.28.1` / PyPI latest `0.28.1` | Outbound Quiver, LLM, and proof HTTP calls | Already used by adapters and by `app.ops.live_proof`. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Uvicorn | repo installed `0.34.0` / PyPI latest `0.39.0` | Serve the ASGI app for real manual POSTs | Use for the actual live operator run. |
| pytest | repo installed `7.1.2` / PyPI latest `8.4.2` | Route, ops, and integration verification | Use for all Phase 20 automation. |
| smtplib / `EmailMessage` | stdlib | SMTP transport behind provider seam | Keep using via `SmtpMailProvider`; do not bypass the provider seam. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reusing `POST /runs/trigger` | New dedicated `/ops/...` trigger route | Adds duplicate runtime behavior and more error paths to maintain. |
| Extending `app.ops.live_proof` | Standalone shell script or one-off curl doc only | Less Python reuse and weaker diagnostics/testing seams. |
| Existing workflow email path | Manual “send memo” helper | Would bypass the actual research-to-email contract the phase must prove. |

**Installation:** No new libraries are needed for planning this phase. Reuse the repo stack already declared in [`pyproject.toml`](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml).

**Version verification:** Verified on 2026-04-03 via local `python -m pip index versions ...` plus PyPI pages. FastAPI `0.128.8` (published 2026-02-11), Pydantic Settings `2.11.0` (published 2025-09-24), Uvicorn `0.39.0` (published 2025-12-21). SQLAlchemy and pytest latest versions were verified via `pip index`; publish dates were not needed to plan this phase because no upgrade is recommended.

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── api/            # Manual trigger route stays here
├── ops/            # Manual-proof helper / preflight should live here
├── workflows/      # Existing persisted engine; reuse only
└── services/       # Readiness and mail seams stay here
tests/
├── api/            # Route-level POST /runs/trigger tests
├── ops/            # Preflight/helper and docs drift tests
└── integration/    # End-to-end manual trigger -> persisted state/email seam
```

### Pattern 1: Reuse The Existing Manual Trigger Route
**What:** Keep Phase 20 anchored to `POST /runs/trigger`, which already creates a manual run record and starts the workflow engine.
**When to use:** For every live and test proof of the narrow Phase 20 path.
**Example:**
```python
# Source: /Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py
@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    runtime = request.app.state.runtime
    run_id = f"run-{uuid4().hex[:8]}"
    runtime.run_service.create_pending_run(
        run_id=run_id,
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )
    state = runtime.workflow_engine.start_run(
        run_id=run_id,
        quiver_client=runtime.create_quiver_client(),
        baseline_report=runtime.run_service.get_latest_report_baseline(exclude_run_id=run_id),
    )
```

### Pattern 2: Keep Manual Proof In `app.ops`, Not In The Route
**What:** Put operator-facing preflight and trigger helpers in `app.ops`, following the existing `live_proof` shape.
**When to use:** For CLI/manual proof ergonomics and staged dependency diagnostics.
**Example:**
```python
# Source: /Users/nickbohm/Desktop/Tinkering/investor/app/ops/live_proof.py
def _trigger_scheduled(settings):
    response = httpx.post(
        settings.schedule_trigger_url,
        headers={"X-Investor-Scheduled-Trigger": settings.scheduled_trigger_token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

### Pattern 3: Let The Workflow Own Research And Mail Delivery
**What:** The proof path should call the normal workflow and let it compose and send the memo.
**When to use:** Always. Do not split research and email into separate manual steps.
**Example:**
```python
# Source: /Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py
email = self._compose_email(state["run_id"], report)
self._mail_provider.send(
    subject=email.subject,
    text_body=email.body,
    html_body=email.html_body,
    recipient=self._settings.daily_memo_to_email,
)
```

### Anti-Patterns to Avoid
- **Second manual workflow path:** Do not add a new runtime path that bypasses `WorkflowEngine.start_run(...)`.
- **Email-only proof shortcut:** Do not add a special “send test email” path and call it Phase 20 completion.
- **Scheduler leakage:** Do not reuse scheduled headers/tokens or the scheduled route as a convenience wrapper.
- **Opaque failure handling:** Do not leave the operator to infer whether Quiver, LLM, SMTP, readiness, or app startup failed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Manual trigger execution | New ad hoc orchestration script that calls research/mail internals directly | `POST /runs/trigger` + `WorkflowEngine.start_run(...)` | The run record, persistence, baseline lookup, and email path already exist. |
| SMTP probe logic | Custom socket/protocol checks | `inspect_smtp_connection(settings)` | Transport mode validation already handles `starttls`/`ssl` constraints. |
| Env readiness checks | Phase-specific placeholder parsing | `collect_readiness_errors(settings)` and `provider_capability_missing(...)` | Startup readiness already codifies placeholder and provider-surface failures. |
| Proof inspection | Custom SQL or log scraping per run | `_inspect_run(settings, run_id)` | Existing tool already returns persisted run status and related counts. |

**Key insight:** The planner should build a thinner operator surface around existing seams, not a new implementation seam.

## Common Pitfalls

### Pitfall 1: Phase 19 Preflight Order Hides The Actual Manual-Run Blocker
**What goes wrong:** `python -m app.ops.live_proof preflight` can abort on Quiver or LLM before SMTP is inspected, so operators misdiagnose the first failing dependency.
**Why it happens:** `_run_preflight(...)` runs Quiver checks and the LLM call before `_check_smtp(...)`.
**How to avoid:** For Phase 20, stage or label preflight checks explicitly by dependency and failure severity.
**Warning signs:** The result never includes `smtp_ready` because Quiver/LLM failed earlier.

### Pitfall 2: Manual Route Errors Are Less Guarded Than Scheduled Route Errors
**What goes wrong:** The manual route currently has no local `try/except`, so a runtime failure bubbles up after the run record is already created.
**Why it happens:** `trigger_run(...)` creates the pending run in one transaction, then calls `start_run(...)` outside route-level error mapping.
**How to avoid:** Plan explicit failure surfacing for the manual proof path and decide whether route behavior, helper behavior, or both should capture and report the partial-run state.
**Warning signs:** A failed direct POST returns 500 while the database still has a `triggered` run with incomplete state.

### Pitfall 3: External Base URL Is Still Rendered Into The Delivered Memo
**What goes wrong:** Even though approval clicking is out of scope, the memo will still include approval/rejection URLs derived from `INVESTOR_EXTERNAL_BASE_URL`.
**Why it happens:** `_compose_email(...)` always calls `_build_approval_url(...)`.
**How to avoid:** Keep the host truthful, but treat reachability as warning/non-blocker if the user’s locked decision says email delivery is the proof target.
**Warning signs:** The memo arrives, but the approval host is placeholder or misleading.

### Pitfall 4: Existing Test Coverage Is Scheduled-Centric
**What goes wrong:** The repo has coverage for scheduled trigger behavior and live-proof helpers, but no current source file for manual route tests.
**Why it happens:** `tests/api/test_scheduling.py` and `tests/integration/test_scheduled_submission_flow.py` focus on the scheduled path, and `tests/api/test_routes.py` is absent.
**How to avoid:** Plan Wave 0 tests for the manual route and manual-proof helper before implementation.
**Warning signs:** A change passes existing tests without ever exercising `POST /runs/trigger`.

## Code Examples

Verified patterns from repo sources and official docs:

### Direct Manual POST Trigger
```python
# Source: /Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py
response = client.post("/runs/trigger")
assert response.status_code == 202
payload = response.json()
assert payload["status"] == "started"
```

### `.env`-Backed Settings Contract
```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

### Test The FastAPI App Through `TestClient`
```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/runs/trigger")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scheduler-centered live proof | Narrow manual POST proof around the existing manual route | Phase 20 scope, 2026-04-03 | Removes cron dependency from the happy path. |
| Hidden env problems discovered during run attempts | Explicit staged preflight/readiness diagnostics | Phase 19-20 ops direction | Better operator feedback and faster live setup. |
| Route-specific duplicate logic for scheduler | Shared workflow/mail engine behind separate trigger surfaces | Existing repo architecture | Manual and scheduled paths can share runtime without sharing trigger semantics. |

**Deprecated/outdated:**
- Treating the scheduled trigger as the default proof path for this phase is outdated relative to the locked Phase 20 decisions.

## Open Questions

1. **Should Phase 20 extend `app.ops.live_proof` or create a dedicated manual-proof helper?**
   - What we know: The existing live-proof CLI already has preflight and inspect seams, but its trigger verb is scheduler-specific.
   - What's unclear: Whether extending that CLI keeps the surface clear enough, or whether a separate `manual_post_proof` helper is simpler.
   - Recommendation: Prefer extending `app.ops.live_proof` unless the command surface becomes confusing.

2. **Should the manual route itself gain better error mapping, or should the helper own the diagnostics?**
   - What we know: The route currently bubbles failures; the helper could still inspect DB state afterward.
   - What's unclear: Whether product/API behavior should change now or remain an ops-only concern.
   - Recommendation: Plan helper-first diagnostics, then only change route behavior if the planner can justify it with tests.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 7.1.2` |
| Config file | [`pyproject.toml`](/Users/nickbohm/Desktop/Tinkering/investor/pyproject.toml) |
| Quick run command | `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/ops/test_live_proof.py tests/integration/test_scheduled_submission_flow.py -q` |
| Full suite command | `PYTHONPATH=. pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PH20-01 | Direct manual POST returns started run metadata and persists `trigger_source="manual"` | api/integration | `PYTHONPATH=. pytest tests/api/test_manual_trigger.py tests/integration/test_manual_trigger_email_flow.py -q` | ❌ Wave 0 |
| PH20-02 | Manual-proof preflight surfaces exact blocker ordering for direct runs | ops/unit | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/ops/test_manual_post_proof.py -q` | ❌ Wave 0 |
| PH20-03 | Manual-proof docs/runbook stay aligned with helper behavior | docs/assertion | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ existing |

### Sampling Rate
- **Per task commit:** `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/ops/test_live_proof.py -q` plus the new Phase 20 test files touched by the task
- **Per wave merge:** `PYTHONPATH=. pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/test_manual_trigger.py` — direct `POST /runs/trigger` success and failure semantics
- [ ] `tests/integration/test_manual_trigger_email_flow.py` — manual trigger -> persisted run/email proof with doubles
- [ ] `tests/ops/test_manual_post_proof.py` — manual preflight/trigger/inspect helper behavior
- [ ] Repo test commands should consistently include `PYTHONPATH=.`; plain `pytest` failed during research with `ModuleNotFoundError: No module named 'app'`

## Sources

### Primary (HIGH confidence)
- Repo source: [`app/api/routes.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/api/routes.py), [`app/workflows/engine.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/workflows/engine.py), [`app/graph/workflow.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/graph/workflow.py), [`app/ops/live_proof.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/ops/live_proof.py), [`app/ops/readiness.py`](/Users/nickbohm/Desktop/Tinkering/investor/app/ops/readiness.py)
- Repo tests: [`tests/api/test_scheduling.py`](/Users/nickbohm/Desktop/Tinkering/investor/tests/api/test_scheduling.py), [`tests/ops/test_live_proof.py`](/Users/nickbohm/Desktop/Tinkering/investor/tests/ops/test_live_proof.py), [`tests/integration/test_scheduled_submission_flow.py`](/Users/nickbohm/Desktop/Tinkering/investor/tests/integration/test_scheduled_submission_flow.py)
- FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/
- Pydantic Settings docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- HTTPX API docs: https://www.python-httpx.org/api/

### Secondary (MEDIUM confidence)
- PyPI package pages used to verify current release versions: https://pypi.org/project/fastapi/ , https://pypi.org/project/pydantic-settings/ , https://pypi.org/project/SQLAlchemy/ , https://pypi.org/project/uvicorn/ , https://pypi.org/project/pytest/
- Local `python -m pip index versions ...` output on 2026-04-03 for FastAPI, Pydantic Settings, SQLAlchemy, HTTPX, Uvicorn, and pytest

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - the phase should reuse the already-present repo stack; no replatforming or new library choice is needed.
- Architecture: HIGH - the repo already implements the direct route and workflow seam; the remaining work is operator tooling and validation.
- Pitfalls: HIGH - they are directly evidenced by current code, current tests, and the recorded Phase 19 live-proof block.

**Research date:** 2026-04-03
**Valid until:** 2026-05-03
