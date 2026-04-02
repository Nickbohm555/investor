# Phase 15: Prove The Live Quiver-To-Email Workflow End To End - Research

**Researched:** 2026-04-02
**Domain:** Live operator-proof execution from Quiver API through OpenAI-compatible synthesis, SMTP delivery, public approval callback, and persisted run-state verification
**Confidence:** MEDIUM

## User Constraints

No `*-CONTEXT.md` exists for Phase 15, so there are no phase-specific locked decisions copied from upstream discussion.

Repo and roadmap constraints that still apply:
- Keep the existing Python/FastAPI/Postgres direction.
- Reuse the current workflow/runtime seams instead of inventing a second live-proof code path.
- Use real Quiver auth, a real OpenAI-compatible `/v1` model endpoint, real SMTP delivery, and a real operator inbox for the proof.
- The approval link must resolve against the configured external base URL and reach the persisted approval callback path without hidden manual glue.
- Repo docs and logs must capture the exact live-proof workflow, failure modes, and any remaining manual steps after email delivery.

Planning-relevant gaps caused by the missing `CONTEXT.md`:
- No locked decision exists yet for how `INVESTOR_EXTERNAL_BASE_URL` will be made publicly reachable from this machine.
- No locked decision exists yet for which SMTP provider/account will send the proof memo.
- No locked decision exists yet for whether the live proof runs via `docker compose` on this host, on another host, or behind an operator-managed tunnel/reverse proxy.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LQE-01 | One real run uses live Quiver auth, a configured OpenAI-compatible model, and real SMTP delivery to send the memo to `INVESTOR_DAILY_MEMO_TO_EMAIL` (`nickbohm555@gmail.com` for the live proof). | Standard Stack, Architecture Pattern 1, Common Pitfalls 1-3, Validation Architecture |
| LQE-02 | The delivered memo contains a working approval link for the configured external base URL, and the callback reaches the expected persisted run state. | Architecture Patterns 2-4, Don't Hand-Roll, Common Pitfalls 4-5, Validation Architecture |
| LQE-03 | Docs and logs capture the exact live-proof workflow, failure modes, and remaining manual steps required after delivery. | Architecture Pattern 5, Common Pitfalls 6-7, Validation Architecture |
</phase_requirements>

## Summary

Phase 15 should not add new business logic before proving the live path. The repo already has the correct execution seam: `POST /runs/trigger/scheduled` creates the persisted run, `WorkflowEngine.start_run()` invokes Quiver plus the OpenAI-compatible model and sends mail, `/approval/{token}` resolves the signed callback against persisted state, and the database already stores run payloads, approval events, transitions, and broker artifacts. Planning should therefore focus on swapping the existing doubles for live credentials and proving that the current route/state/log contracts still hold under real external services.

The main risk is operational, not architectural. A live proof now depends on four external facts being true at the same time: Quiver credentials work against the intended endpoints, the configured model endpoint supports `/v1/chat/completions` plus tool calling, SMTP credentials can deliver to the target inbox, and `INVESTOR_EXTERNAL_BASE_URL` really reaches this app's `/approval/{token}` route. The repo is already explicit about one current blocker: this machine has another container binding host port `8000`, so the default Compose host mapping cannot currently expose the app directly here without either freeing that port, remapping it, or putting the app behind a reachable proxy/tunnel.

The most important planning choice is to keep the live proof on the same contract the dry run already exercises. Do not create a new "Phase 15 smoke path" that bypasses `app.main`, the FastAPI routes, or the existing persisted run records. Instead, add a live-proof runbook plus a narrowly scoped verification path that checks three things after a real delivery: the operator inbox received the memo, the memo link resolves to `/approval/{token}` on the configured public base URL, and the run record plus approval/state-transition records reflect the expected end state.

**Primary recommendation:** Reuse the existing scheduled-trigger -> persisted run -> SMTP memo -> signed approval URL -> persisted approval-state path, and plan Phase 15 around environment/infrastructure readiness plus auditable live-proof logging, not around new orchestration code.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.3 | Owns `/runs/trigger/scheduled`, `/approval/{token}`, `/runs/{run_id}/execute`, and `/health` | The live proof should exercise the actual API surface already used by the app |
| SQLAlchemy | 2.0.48 | Persists run records, approval events, transitions, recommendation rows, and broker artifacts | Persisted DB truth is already the source of record for proof verification |
| pydantic-settings | 2.13.1 | Loads the env-backed contract for SMTP, Quiver, OpenAI-compatible model, external URL, and tokens | The live proof is fundamentally an env-readiness and runtime-composition exercise |
| httpx | 0.28.1 | Powers the Quiver client and HTTP-based OpenAI-compatible adapter | The repo already uses one adapter style for both external API surfaces |
| pytest | 9.0.2 | Existing regression suite for scheduled trigger, docs, and scheduled-submission flow | Planning should extend this validation surface, not replace it |
| Uvicorn | 0.42.0 | Serves the live app process behind the public callback URL | Live approval proof requires the real app server to be reachable |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `smtplib` | stdlib (3.12) | Real SMTP delivery with STARTTLS and login | Use for the proof exactly as implemented in `SmtpMailProvider` |
| Jinja2 | 3.1.6 | Renders the text and HTML strategic memo templates | Use whenever memo content needs to be inspected or debugged |
| psycopg | 3.3.3 | Connects to Postgres in the Compose/runtime path and migrations | Use for the live proof's persisted-state checks |
| Docker Compose | repo runtime | Starts `postgres`, `migrate`, and `app` with the repo-owned runtime wiring | Use if the live proof stays on the documented container path |
| Operator-managed public tunnel or reverse proxy | external infra | Makes `INVESTOR_EXTERNAL_BASE_URL` reachable to the approval route | Use only if host-direct exposure is unavailable or undesirable |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Existing scheduled trigger and approval routes | Ad hoc scripts that call services directly | Faster to hack, but it would not prove the repo's real operator-visible runtime contract |
| Existing SMTP provider seam | Console/mock transport for convenience | Violates the phase goal; the point is proving real delivery |
| Existing persisted approval callback | Manual DB edits or direct workflow-engine calls | Hides the most failure-prone live operator boundary |
| Existing Compose/app runtime | One-off notebook or standalone Python script | Useful for debugging, but not sufficient for the actual end-to-end proof |

**Installation / verification commands:**
```bash
pip install -e .
PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q
docker compose up -d --build
docker compose logs -f migrate app
```

**Version verification:** Verified against PyPI JSON on 2026-04-02.

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
├── api/routes.py              # scheduled trigger, approval callback, execution endpoint
├── config.py                  # env-backed live runtime contract
├── runtime.py                 # compose real adapters vs doubles
├── services/mail_provider.py  # SMTP transport
├── services/research_llm.py   # OpenAI-compatible /v1 chat-completions adapter
├── tools/quiver.py            # Quiver HTTP client
├── repositories/runs.py       # persisted proof state queries
├── db/models.py               # run / approval / transition / artifact tables
└── ops/                       # readiness checks and dry-run harness
tests/
├── api/                       # route-level contracts
├── integration/               # multi-step proof with persisted assertions
└── ops/                       # operator docs/runtime checks
.planning/phases/15-.../
└── 15-RESEARCH.md             # planner input
```

### Pattern 1: Swap Only External Adapters, Keep the Route/State Path Identical

**What:** The live proof should use the same `create_app()` composition, route handlers, workflow engine, and repositories as the dry run. The only thing that changes is that the app uses real Quiver, real OpenAI-compatible model credentials, real SMTP, and a reachable external base URL.

**When to use:** Always for Phase 15.

**Example:**
```python
# Source: repo pattern in app/runtime.py
research_node = ResearchNode(
    llm=HttpResearchLLM(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    ),
)
mail_provider = mail_provider or SmtpMailProvider(settings)

def create_quiver_client(self) -> QuiverClient:
    return QuiverClient(
        base_url=self.settings.quiver_base_url,
        api_key=self.settings.quiver_api_key,
        transport=self.quiver_transport,
    )
```

### Pattern 2: Treat the Approval URL as an Infrastructure Contract, Not Just a String Setting

**What:** `external_base_url` is not merely documentation. The memo renders a signed token URL from it, so the configured value must terminate at the running app and preserve the `/approval/{token}` path.

**When to use:** For all live-proof setup and debugging.

**Example:**
```python
# Source: repo pattern in app/graph/workflow.py
approval_url=self._build_approval_url(run_id, "approve")
rejection_url=self._build_approval_url(run_id, "reject")

def _build_approval_url(self, run_id: str, decision: str) -> str:
    token = issue_approval_token(...)
    return f"{self._settings.external_base_url.rstrip('/')}/approval/{token}"
```

### Pattern 3: Verify the Live Proof From Persisted Database Truth

**What:** After the operator clicks the delivered link, verify success through `runs`, `approval_events`, and `state_transitions`, not only through browser behavior or HTTP 200s.

**When to use:** For the live proof checklist, logs, and any recovery/debugging.

**Example:**
```python
# Source: repo pattern in app/repositories/runs.py
repository.record_approval_event(
    run_id=run.run_id,
    decision=payload.decision,
    token_id=token_id,
)
repository.transition_run(
    run,
    to_status=result["status"],
    current_step=result["current_step"],
    approval_status=event.split(":", 1)[1],
    reason=f"Workflow advanced via {event}",
)
```

### Pattern 4: Keep the Scheduled Trigger as the Live-Proof Entry Point

**What:** The most truthful live proof starts at `POST /runs/trigger/scheduled` with the configured trigger token, because this is the operator-facing production trigger seam and already logs duplicate/start/failure outcomes.

**When to use:** For the real proof run and for failure reproduction unless a manual-trigger fallback is explicitly documented.

**Example:**
```python
# Source: repo pattern in app/api/routes.py
if scheduled_trigger != runtime.settings.scheduled_trigger_token:
    raise HTTPException(status_code=401, detail="Invalid scheduled trigger token")
...
logger.info(
    "scheduled_trigger result=started schedule_key=%s run_id=%s",
    run.schedule_key,
    run.run_id,
)
```

### Pattern 5: Log the Live Proof as an Operator Runbook, Not Just a Test Result

**What:** The planner should require one durable artifact that captures the exact env assumptions, trigger command, expected logs, inbox verification step, approval-click step, and persisted-state checks, plus how to recover from each common failure.

**When to use:** For docs and completion criteria.

**Example:**
```text
1. Start runtime and confirm /health.
2. Trigger scheduled route with the configured token.
3. Watch logs for scheduled_trigger result=started and memo_delivery result=sent.
4. Confirm the memo arrived at INVESTOR_DAILY_MEMO_TO_EMAIL.
5. Click the delivered approval link.
6. Query persisted run, approval_event, and transition records for the run_id.
```

### Anti-Patterns to Avoid

- **A separate Phase 15-only runner:** Do not add a standalone script that bypasses FastAPI routes or runtime composition.
- **Success defined only by inbox delivery:** The proof is incomplete until the approval callback and persisted state are verified.
- **Using a localhost-only approval URL:** A delivered email with `http://127.0.0.1` or an unreachable host does not satisfy the phase.
- **Relying on console inspection alone:** Logs help, but persisted DB state is the final truth source.
- **Changing workflow behavior to fit the live proof:** Fix environment and infrastructure first; keep product logic stable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMTP protocol details | Custom socket/TLS/mail MIME implementation | Python `smtplib` + `EmailMessage` | STARTTLS, auth, and multipart composition are already handled by the stdlib path in use |
| Public callback exposure | Custom webhook relay or polling mechanism | Existing HTTPS reverse proxy or operator-managed tunnel to the FastAPI app | The approval link already expects a direct inbound HTTP callback |
| Run-state proof | Ad hoc JSON files or screenshots as the primary audit | Existing Postgres `runs`, `approval_events`, `state_transitions`, `broker_artifacts` tables | The app already persists the exact state the phase needs to prove |
| Duplicate suppression | Shell locking or trigger-side coordination | Existing unique `schedule_key` in Postgres plus route logging | The repo already enforces "one primary run per schedule key" in the correct place |
| LLM transport contract | Provider-specific SDK rewrite for this proof | Existing OpenAI-compatible `HttpResearchLLM` contract | The repo has already standardized on `/v1/chat/completions` plus tool-calling messages |

**Key insight:** Phase 15 is not a feature-build phase. It is a truthfulness phase. Reuse every proven seam and prove them under live credentials.

## Common Pitfalls

### Pitfall 1: The OpenAI-Compatible Endpoint Is Not Actually Compatible Enough

**What goes wrong:** The configured model endpoint accepts basic chat requests but fails on tool calls, `tools`, or `parallel_tool_calls`, causing the research loop to fail mid-run.

**Why it happens:** The repo's adapter expects `/v1/chat/completions` compatibility, not just any text-generation endpoint.

**How to avoid:** Preflight the selected provider/model with a minimal chat-completions plus tool-calling request before the live proof.

**Warning signs:** Readiness passes the `/v1` suffix check, but the live run fails during Quiver-loop tool usage.

### Pitfall 2: Quiver's Published OpenAPI Surface Does Not Fully Match the Repo's Live Endpoint Assumptions

**What goes wrong:** The repo calls `/beta/live/congresstrading`, `/beta/live/insiders`, `/beta/live/govcontracts`, and `/beta/live/lobbying`, but the current published OpenAPI file documents `live/insiders`, `bulk/congresstrading`, and `historical/lobbying`, and does not currently document `live/govcontracts`.

**Why it happens:** Quiver's public plugin/openapi surface appears narrower than the repo's current endpoint usage.

**How to avoid:** Add a Phase 15 preflight that authenticates and verifies each exact endpoint the repo uses before starting the operator-visible run.

**Warning signs:** A live run fails on only one Quiver dataset while the others succeed, or a 404/401 appears for a path that the repo assumes exists.

### Pitfall 3: SMTP Delivery Succeeds Locally but Mail Never Lands in the Operator Inbox

**What goes wrong:** The app logs a send attempt, but the message is rejected, spam-filtered, or blocked by provider policy.

**Why it happens:** SMTP success is not just host/port/auth; sender identity, TLS policy, and provider restrictions matter.

**How to avoid:** Require a real inbox delivery confirmation in the acceptance checklist and capture provider-side failure signals from app logs.

**Warning signs:** `memo_delivery result=failure` in logs, missing mail in inbox/spam, or provider auth/TLS errors.

### Pitfall 4: `INVESTOR_EXTERNAL_BASE_URL` Is Reachable in Theory but Not From the Delivered Email Context

**What goes wrong:** The link looks valid, but clicking it from Gmail or another mail client fails because the host/port/path is not publicly routable.

**Why it happens:** Localhost, private LAN addresses, or a host port conflict are treated as if they were a public URL.

**How to avoid:** Verify the full approval URL externally before the proof email is sent, including path reachability to `/approval/{token}`.

**Warning signs:** Browser timeouts, connection refused, TLS warnings, or links targeting `127.0.0.1`, a private IP, or a blocked host port.

### Pitfall 5: The Host Port Binding on This Machine Is Already Taken

**What goes wrong:** `docker compose up` cannot expose the app on `0.0.0.0:8000`, so the configured external base URL cannot reach the runtime as documented.

**Why it happens:** Another container on this machine already owns host port `8000`.

**How to avoid:** Decide in planning whether to stop the conflicting service, remap the investor app host port and corresponding external URL, or run behind a separate proxy/tunnel.

**Warning signs:** Compose startup fails or the app is healthy inside the container but unreachable on the configured host URL.

### Pitfall 6: The Live Proof Is Not Reproducible Because Manual Steps Stay Implicit

**What goes wrong:** The operator gets the email once, but nobody can repeat the run later because the exact commands, env assumptions, or callback verification steps were not written down.

**Why it happens:** Live proofs often end as tribal knowledge instead of runbooks.

**How to avoid:** Make docs/log capture part of the implementation plan, not a post-hoc afterthought.

**Warning signs:** Success depends on "remembering what worked last time" or checking only terminal scrollback.

### Pitfall 7: Pytest Commands Drift From the Actual Dev Environment

**What goes wrong:** Phase validation appears broken because the test command omits `PYTHONPATH=.`, even though the tests themselves still pass once imports are configured correctly.

**Why it happens:** The repo is not installed in editable mode by default when running raw `pytest`.

**How to avoid:** Standardize Phase 15 validation commands on either `pip install -e .` first or `PYTHONPATH=. pytest ...`.

**Warning signs:** `ModuleNotFoundError: No module named 'app'` during collection.

## Code Examples

Verified patterns from official sources and current repo seams:

### SMTP STARTTLS + Login
```python
# Source: https://docs.python.org/3/library/smtplib.html
import smtplib
import ssl

with smtplib.SMTP(host, 587, timeout=30) as client:
    client.starttls(context=ssl.create_default_context())
    client.login(username, password)
    client.send_message(message)
```

### FastAPI TestClient Route Proof
```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/runs/trigger/scheduled", headers=headers)
assert response.status_code == 202
```

### Unique Schedule-Key Enforcement
```sql
-- Source: https://www.postgresql.org/docs/current/indexes-unique.html
CREATE UNIQUE INDEX uq_runs_schedule_key ON runs (schedule_key);
```

### OpenAI-Compatible Chat Completions Request Shape
```python
# Source: repo seam in app/services/research_llm.py
body = {
    "model": self._model,
    "messages": messages,
    "tools": tools,
    "tool_choice": "auto",
    "parallel_tool_calls": False,
}
response = self._client.post("/chat/completions", json=body)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dry-run-only workflow proof with injected doubles | One real operator-visible proof using the same runtime seams plus live credentials | Phase 15 scope, 2026-04-02 roadmap state | Phase acceptance now depends on real delivery and callback, not just local deterministic proofs |
| Treating any text-generation endpoint as sufficient | Require an OpenAI-compatible `/v1/chat/completions` endpoint with tool-calling support | Current repo runtime contract in `HttpResearchLLM` | Provider selection must be validated before the live run |
| Treating Quiver support as a generic API capability | Verify the exact endpoint paths the repo calls | Current Quiver plugin/openapi docs inspected on 2026-04-02 | Planning must include endpoint-level preflight, especially for `govcontracts` |

**Deprecated / outdated for this phase:**
- `python -m app.ops.dry_run` as the final proof: it remains the fastest regression check, but it is not sufficient evidence for Phase 15 completion.
- Localhost-only callback assumptions: the roadmap now requires a real delivered approval link against the configured external base URL.

## Open Questions

1. **What public URL will back `INVESTOR_EXTERNAL_BASE_URL` for the proof?**
   - What we know: the repo generates links from that setting, and this host currently has another container occupying port `8000`.
   - What's unclear: whether the proof will use a freed host port, a remapped port plus updated base URL, or an external reverse proxy/tunnel.
   - Recommendation: make this a Wave 0 planning decision before any live-run task is scheduled.

2. **Which exact model provider and model will satisfy the repo's OpenAI-compatible contract?**
   - What we know: the repo requires `/v1/chat/completions` and tool-calling-compatible request fields.
   - What's unclear: which actual provider/model will be used for the live run and whether it supports the repo's Quiver loop behavior.
   - Recommendation: add a provider preflight task that performs a minimal authenticated tool-calling request before the full proof.

3. **Do the exact Quiver endpoints used by the repo work with the intended account today?**
   - What we know: the repo uses four live endpoints; Quiver's current published plugin/openapi file documents only part of that surface.
   - What's unclear: whether `live/govcontracts` and the repo's other exact paths remain valid for the target account.
   - Recommendation: add an authenticated endpoint smoke check that logs HTTP status and row counts for each required path.

4. **Will SMTP provider policy permit the chosen sender/from identity to deliver to Gmail?**
   - What we know: the repo's SMTP code uses STARTTLS on port 587 and optional login.
   - What's unclear: whether the chosen account supports the configured sender and whether Gmail delivery will land cleanly.
   - Recommendation: include one preflight mail send to the target inbox before the full workflow run, then proceed to the integrated proof.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` 9.0.2 |
| Config file | none |
| Quick run command | `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q` |
| Full suite command | `PYTHONPATH=. pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LQE-01 | Scheduled trigger creates a real run path and sends a memo through the active provider seam | integration + manual live proof | `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py -q` | ✅ |
| LQE-02 | Approval link resolves the same persisted run and advances stored state | integration + manual live proof | `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py -q` | ✅ |
| LQE-03 | Operator docs and runtime instructions stay aligned with the shipped workflow | ops/docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q`
- **Per wave merge:** `PYTHONPATH=. pytest -q`
- **Phase gate:** Full suite green plus one documented live proof run before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] Add a live-proof preflight script or documented commands for Quiver endpoint auth/status validation.
- [ ] Add a live-proof preflight script or documented commands for OpenAI-compatible tool-calling validation.
- [ ] Add a documented SMTP/inbox verification step before the integrated proof run.
- [ ] Add a persisted-state inspection command or script for `runs`, `approval_events`, and `state_transitions` by `run_id`.
- [ ] Add explicit docs for how `INVESTOR_EXTERNAL_BASE_URL` is made publicly reachable in the proof environment.

## Sources

### Primary (HIGH confidence)

- Quiver Quantitative plugin manifest - https://api.quiverquant.com/.well-known/ai-plugin.json - verified auth mode and official OpenAPI location
- Quiver Quantitative OpenAPI - https://api.quiverquant.com/static/openapi.yaml - verified currently published endpoint groups and documented response fields
- Python `smtplib` docs - https://docs.python.org/3/library/smtplib.html - checked STARTTLS, login, and send-message behavior
- FastAPI testing docs - https://fastapi.tiangolo.com/tutorial/testing/ - checked `TestClient` pattern for route-level proof
- PostgreSQL unique indexes docs - https://www.postgresql.org/docs/current/indexes-unique.html - checked the unique-index pattern behind schedule-key dedupe

### Secondary (MEDIUM confidence)

- OpenAI Chat Completions API reference - https://platform.openai.com/docs/api-reference/chat/create - used as the official reference URL for the repo's current `/v1/chat/completions` contract, but direct page fetch was blocked from the terminal
- OpenAI text generation guide - https://platform.openai.com/docs/guides/gpt/chat-completions-api - used as the official guide URL for current chat-completions positioning, with search-based verification only

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified directly from the repo runtime plus current package registry data
- Architecture: HIGH - derived from current repo code paths that already implement the dry-run and scheduled/approval seams
- Pitfalls: MEDIUM - most are verified by code and docs, but the Quiver endpoint mismatch and provider-specific live behavior still need authenticated proof

**Research date:** 2026-04-02
**Valid until:** 2026-04-09
