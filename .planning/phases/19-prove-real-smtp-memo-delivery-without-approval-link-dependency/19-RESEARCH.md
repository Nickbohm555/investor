# Phase 19: Prove Real SMTP Memo Delivery Without Approval-Link Dependency - Research

**Researched:** 2026-04-03
**Domain:** Live SMTP memo proof, live-proof CLI gating, and operator verification when approval-link reachability is unavailable
**Confidence:** HIGH

## User Constraints

No `*-CONTEXT.md` exists for Phase 19, so there are no phase-specific locked decisions copied from upstream discussion.

Repo and roadmap constraints that still apply:
- Keep the existing Python/FastAPI/Postgres direction.
- Reuse the current scheduled-trigger -> workflow -> SMTP memo path instead of inventing a second proof-only runtime.
- Prove real SMTP memo delivery even when `INVESTOR_EXTERNAL_BASE_URL` is not currently reachable.
- Do not turn "SMTP proof" into "approval callback proof"; those are now separate operational questions.
- Keep proof artifacts repo-owned: CLI output, runbook, result template, logs, and persisted run inspection.

Planning-relevant gaps caused by the missing `CONTEXT.md`:
- No locked decision exists yet for whether Phase 19 should update the existing Phase 15 live-proof assets in place or create Phase 19-specific runbook/result assets.
- No locked decision exists yet for which SMTP provider/account will be used for the proof.
- No locked decision exists yet for whether SMTP proof should require Quiver and LLM live credentials in the same run, or whether a mail-focused replay/redrive path is acceptable.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SMTP-19-01 | Operators can trigger one real memo send through the existing scheduled route and verify delivery in the target inbox without requiring a reachable approval callback host. | Summary, Architecture Patterns 1-3, Common Pitfalls 1-2, Validation Architecture |
| SMTP-19-02 | Live-proof tooling reports SMTP readiness and approval-link reachability as separate statuses, with approval reachability treated as non-blocking for this phase's proof objective. | Summary, Architecture Patterns 2 and 4, Common Pitfalls 1 and 4, Validation Architecture |
| SMTP-19-03 | The delivered memo still includes the configured approval-link host, but Phase 19 proof only requires host-string verification, not callback execution. | Architecture Patterns 3-4, Common Pitfalls 1 and 5, Validation Architecture |
| SMTP-19-04 | SMTP proof supports the provider's actual TLS mode or explicitly fails fast with a clear diagnostic when the provider requires unsupported transport behavior. | Standard Stack, Common Pitfalls 3 and 6, Code Examples, Validation Architecture |
</phase_requirements>

## Summary

Phase 19 should be planned as a scope split, not a new mail subsystem. The current runtime already sends the memo independently of callback reachability: `CompiledInvestorWorkflow._compose_email()` renders approval URLs from `external_base_url`, `SmtpMailProvider.send()` opens an SMTP connection and sends the multipart message, and the scheduled route returns `started` after the workflow completes. Nothing in the send path requires the approval URL to be publicly reachable. The dependency exists in the live-proof tooling and runbook, not in the product logic.

That makes the main planning change straightforward: separate "can we deliver the memo?" from "can the approval link be used right now?" The current `python -m app.ops.live_proof preflight` reports `reachability_check`, and the current Phase 15 runbook treats an unreachable approval boundary as a hard stop before trigger. For Phase 19, that coupling is wrong. SMTP proof should still run through the real scheduled trigger and real memo rendering, but preflight should classify callback reachability as a warning or secondary status instead of a blocker.

The most important implementation risk is SMTP transport mode. Today both `app/services/mail_provider.py` and `app/ops/live_proof.py` assume explicit STARTTLS only when `smtp_port == 587`. Official Python docs distinguish STARTTLS on `SMTP` from implicit TLS on `SMTP_SSL`. If the selected provider requires port `465`, the current code will mis-handle the connection and produce a false operational dead end. Plan Phase 19 to either add explicit `smtp_security`/port-aware implicit TLS handling or document that only STARTTLS-on-587 is supported and fail fast with a clear diagnostic.

**Primary recommendation:** Keep the real scheduled-trigger -> memo-render -> SMTP delivery path, but change the live-proof contract so approval-link reachability is recorded separately from SMTP proof and does not block Phase 19 success.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.3 | Owns `/runs/trigger/scheduled`, `/approval/{token}`, and `/health` | Phase 19 should prove the existing HTTP entrypoint instead of a proof-only mail script |
| SQLAlchemy | 2.0.49 | Persists the run row used to correlate the delivered memo with logs and later inspection | Persisted run truth remains the audit anchor even when approval is skipped |
| pydantic-settings | 2.13.1 | Loads SMTP, trigger, and external-base-url envs from `.env` | Phase 19 is mostly an operational contract over existing env-backed settings |
| httpx | 0.28.1 | Drives preflight checks and scheduled-trigger HTTP calls | Keep live-proof probing and route-triggering on the repo's existing HTTP client |
| pytest | 9.0.2 | Existing test framework for ops/docs/integration coverage | Phase 19 is a contract-and-docs phase and needs red/green coverage on those surfaces |
| Python `smtplib` + `email.message.EmailMessage` | stdlib (Python 3.12/3.14 docs checked) | Real SMTP transport and multipart memo composition | This is already the repo's transport seam and the standard-library path is sufficient here |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Uvicorn | 0.43.0 | Serves the real app process for trigger and health routes | Use for any live proof that runs the shipped app surface |
| psycopg | 3.3.3 | Connects to Postgres in the Compose runtime | Use for persisted run inspection after send |
| Jinja2 | 3.1.6 | Renders the HTML/text memo body | Use when debugging delivered memo content or link rendering |
| Docker Compose | repo runtime | Starts `postgres`, `migrate`, and `app` | Use if the proof stays on the documented runtime path |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Real scheduled trigger and workflow memo send | Standalone "send test email" CLI | Easier to debug transport, but it does not prove the app's real memo-rendering or scheduled-route contract |
| One preflight result with a hard reachability gate | Split readiness into SMTP/blocking vs approval/non-blocking statuses | Slightly more complexity, but it matches the actual phase goal and avoids false blockers |
| Current STARTTLS-only logic | Port-aware `SMTP`/`SMTP_SSL` branching or explicit `smtp_security` config | Needed if the chosen provider uses implicit TLS on 465 |

**Installation:**
```bash
pip install -e .
```

**Version verification:** Verified against current PyPI package metadata on 2026-04-03.

| Package | Latest | Published |
|---------|--------|-----------|
| FastAPI | 0.135.3 | 2026-04-01 |
| SQLAlchemy | 2.0.49 | 2026-04-03 |
| pydantic-settings | 2.13.1 | 2026-02-19 |
| httpx | 0.28.1 | 2024-12-06 |
| Uvicorn | 0.43.0 | 2026-04-03 |
| psycopg | 3.3.3 | 2026-02-18 |
| Jinja2 | 3.1.6 | 2025-03-05 |
| pytest | 9.0.2 | 2025-12-06 |

## Architecture Patterns

### Recommended Project Structure

```text
app/
├── api/routes.py              # existing scheduled trigger and approval callback
├── config.py                  # env-backed SMTP and external-base-url contract
├── graph/workflow.py          # memo rendering and approval-link composition
├── ops/live_proof.py          # repo-owned proof CLI, likely updated for split readiness
└── services/mail_provider.py  # real SMTP transport
tests/
├── integration/               # scheduled-trigger path remains the integration seam
├── ops/                       # live-proof CLI and docs/runbook assertions
└── services/                  # SMTP transport-mode coverage
.planning/phases/19-.../
└── 19-RESEARCH.md             # planner input
```

### Pattern 1: Keep The Existing Scheduled Trigger As The Proof Entry Point

**What:** Phase 19 should still start from `POST /runs/trigger/scheduled` and let the existing workflow render and send the memo.

**When to use:** Always for the real SMTP proof.

**Example:**
```python
# Source: repo pattern in app/api/routes.py
state = runtime.workflow_engine.start_run(
    run_id=run.run_id,
    quiver_client=runtime.create_quiver_client(),
    baseline_report=baseline_report,
)
```

### Pattern 2: Split Proof Status Into Blocking And Non-Blocking Gates

**What:** Preflight should report SMTP connectivity/readiness separately from approval-link reachability. For Phase 19, unreachable approval callback should not block the real send attempt.

**When to use:** In `app.ops.live_proof` and the runbook/result template.

**Example:**
```python
# Source: project adaptation over app/ops/live_proof.py
return {
    "smtp_check": smtp_check,
    "smtp_ready": smtp_check["reachable"],
    "reachability_check": reachability_check,
    "approval_reachability_ready": reachability_check["reachable"],
    "blocking_failures": ["smtp"] if not smtp_check["reachable"] else [],
    "warnings": ["approval-link-unreachable"] if not reachability_check["reachable"] else [],
}
```

### Pattern 3: Keep Approval Links In The Delivered Memo, But Do Not Require Clicking Them

**What:** The email should still render `external_base_url`-based links. Phase 19 only needs to verify the host value in the delivered message, not callback success.

**When to use:** For result-template fields and manual verification steps.

**Example:**
```python
# Source: repo pattern in app/graph/workflow.py
def _build_approval_url(self, run_id: str, decision: str) -> str:
    token = sign_approval_token(...)
    return f"{self._settings.external_base_url.rstrip('/')}/approval/{token}"
```

### Pattern 4: Treat SMTP Transport Mode As Config, Not An Implicit Port Guess

**What:** The current logic only upgrades to TLS when `smtp_port == 587`. Phase 19 planning should explicitly decide whether to support implicit TLS (`SMTP_SSL`) as well.

**When to use:** Before choosing the proof mailbox/provider and before changing the proof runbook.

**Example:**
```python
# Source: https://docs.python.org/3/library/smtplib.html
import smtplib
import ssl

context = ssl.create_default_context()

with smtplib.SMTP_SSL(host, 465, context=context, timeout=30) as client:
    client.login(username, password)
    client.send_message(message)
```

### Pattern 5: Record SMTP Proof As Operator Evidence, Not Just CLI JSON

**What:** Phase 19 should leave behind a runbook/result artifact that records `run_id`, recipient, approval-link host as rendered, observed `memo_delivery result=sent` log line, and whether callback reachability was available.

**When to use:** For completion criteria and future operator debugging.

**Example:**
```text
run_id: run-1234abcd
memo_delivered_to: operator@example.com
approval_link_host: https://investor.example.com
approval_callback_status: skipped-for-phase-19
memo_delivery_log_line: memo_delivery result=sent provider=smtp recipient=operator@example.com
```

### Anti-Patterns to Avoid

- **Adding an SMTP-only proof script:** It would bypass the real memo-rendering and scheduled-route contract.
- **Keeping approval reachability as a hard preflight gate:** That reproduces the current false blocker and defeats the purpose of Phase 19.
- **Counting SMTP login as delivery proof:** Connect/login only proves auth and transport setup, not inbox delivery.
- **Assuming all providers use STARTTLS on 587:** Many providers still use implicit TLS on 465.
- **Dropping approval links from the memo just to make the proof easier:** The memo contract should remain truthful; only the proof criteria should narrow.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMTP transport | Custom socket/TLS/MIME code | `smtplib` + `EmailMessage` | The stdlib already covers login, multipart messages, STARTTLS, and implicit TLS |
| Memo proof path | Separate mail-debug runner | Existing scheduled trigger and workflow engine | Phase 19 is about proving the product path, not a side channel |
| Approval proof substitution | Manual DB edits or fake callback writes | Delivered-email inspection plus persisted run/log verification | The phase explicitly removes callback dependency, not truthfulness |
| Reachability diagnostics | Ad hoc shell checks scattered in docs | Repo-owned preflight JSON plus runbook/result template | Operators need one repeatable surface |

**Key insight:** The right split is "same send path, narrower success criteria," not "different code path for mail."

## Common Pitfalls

### Pitfall 1: Treating Callback Reachability As A Requirement For Sending

**What goes wrong:** Preflight or docs tell the operator to stop before trigger when `INVESTOR_EXTERNAL_BASE_URL` is unreachable, even though the memo could still be sent.

**Why it happens:** The current Phase 15 runbook couples proof-of-delivery with proof-of-callback.

**How to avoid:** Make callback reachability a separately reported status and mark it non-blocking for Phase 19.

**Warning signs:** `scheduled_trigger` is never attempted even though SMTP credentials and the app runtime are ready.

### Pitfall 2: Proving Only SMTP Auth Instead Of Inbox Delivery

**What goes wrong:** A successful `_check_smtp()` connect/login is treated as success even though no memo was actually delivered.

**Why it happens:** The existing preflight intentionally stops short of sending mail.

**How to avoid:** Require one real scheduled-triggered memo send and manual inbox confirmation.

**Warning signs:** Preflight is green but there is no `memo_delivery result=sent` log line and no delivered memo.

### Pitfall 3: SMTP Provider Uses Implicit TLS On 465

**What goes wrong:** The current code opens `smtplib.SMTP(host, 465)` and never upgrades to TLS because it only calls `starttls()` on port `587`.

**Why it happens:** The transport logic infers security mode from one port check instead of supporting both standard modes.

**How to avoid:** Add explicit support for `SMTP_SSL` or fail fast with a provider-mode diagnostic before the live proof.

**Warning signs:** Connection failures or protocol errors only when using a 465-based provider.

### Pitfall 4: Updating CLI Behavior Without Updating The Runbook And Result Template

**What goes wrong:** The code records callback reachability as optional, but docs/tests still require `approval_probe_*` as a blocking step.

**Why it happens:** Ops drift tests currently encode the Phase 15 contract.

**How to avoid:** Plan docs, result-template, and test updates in the same wave as the CLI contract change.

**Warning signs:** `tests/ops/test_operational_docs.py` still asserts the old runbook flow.

### Pitfall 5: Removing Approval-Link Rendering Instead Of Narrowing Proof Criteria

**What goes wrong:** The workflow stops including approval links just to make the SMTP proof pass without external infrastructure.

**Why it happens:** It is easier than changing the proof contract.

**How to avoid:** Keep link rendering untouched and verify only the rendered host in the delivered memo.

**Warning signs:** `app/graph/workflow.py` or email templates are modified to hide approval/rejection URLs.

### Pitfall 6: Live Provider Choice Forces An Unsupported SMTP Mode

**What goes wrong:** The selected provider/account requires security or auth behavior the code does not support.

**Why it happens:** Provider selection is made before checking the repo's transport constraints.

**How to avoid:** Choose a STARTTLS-compatible provider/account or include transport-mode support in the plan.

**Warning signs:** The chosen provider docs recommend port 465 only, or OAuth-only auth, while the repo expects username/password SMTP.

## Code Examples

Verified patterns from official sources:

### Multipart Memo Composition
```python
# Source: https://docs.python.org/3/library/email.message.html
from email.message import EmailMessage

message = EmailMessage()
message["Subject"] = subject
message["From"] = sender
message["To"] = recipient
message.set_content(text_body)
message.add_alternative(html_body, subtype="html")
```

### STARTTLS SMTP Send
```python
# Source: https://docs.python.org/3/library/smtplib.html
import smtplib
import ssl

with smtplib.SMTP(host, 587, timeout=30) as client:
    client.starttls(context=ssl.create_default_context())
    client.login(username, password)
    client.send_message(message)
```

### Implicit TLS SMTP Send
```python
# Source: https://docs.python.org/3/library/smtplib.html
import smtplib
import ssl

with smtplib.SMTP_SSL(host, 465, context=ssl.create_default_context(), timeout=30) as client:
    client.login(username, password)
    client.send_message(message)
```

## State Of The Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| One live-proof contract that blocks on approval-host reachability before trigger | Split proof objective: SMTP memo delivery can be proven independently, while callback reachability is reported separately | Recommended for Phase 19 planning on 2026-04-03 | Removes a false blocker and lets operators prove the mail path earlier |
| Implicit assumption that SMTP == STARTTLS on 587 | Explicit recognition that standard-library SMTP supports both STARTTLS (`SMTP`) and implicit TLS (`SMTP_SSL`) | Python stdlib docs, current as of 2026-04-03 | Provider selection and transport logic must be aligned before the proof |

**Deprecated/outdated:**
- "Preflight must stop if approval probe is unreachable" for SMTP-only proof work. Keep that rule for callback-proof phases, not for Phase 19.

## Open Questions

1. **Should Phase 19 update Phase 15 assets in place or create Phase 19-specific proof assets?**
   - What we know: `README.md` and `tests/ops/test_operational_docs.py` currently point at Phase 15 assets.
   - What's unclear: Whether the project wants one evolving live-proof contract or separate historical proof tracks.
   - Recommendation: Prefer Phase 19-specific runbook/result artifacts and then update README to point to the current proof objective.

2. **Does the chosen SMTP provider require implicit TLS on 465 or STARTTLS on 587?**
   - What we know: Current code only supports STARTTLS on 587.
   - What's unclear: The actual provider/account to be used for the proof.
   - Recommendation: Decide provider first; if it is 465-based, include transport support in Wave 0.

3. **Must the Phase 19 proof still use live Quiver and live LLM credentials?**
   - What we know: The current scheduled route drives the full workflow, so real memo delivery normally implies those providers are also live.
   - What's unclear: Whether Phase 19 allows replay/redrive or a narrower mail-focused path to avoid unrelated provider blockers.
   - Recommendation: Prefer the real scheduled path if credentials exist; otherwise explicitly decide whether a mail-enabled replay/redrive is acceptable.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.2` |
| Config file | none |
| Quick run command | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/ops/test_operational_docs.py -q` |
| Full suite command | `PYTHONPATH=. pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SMTP-19-01 | One real scheduled-trigger proof path remains the source of truth for memo send | integration + ops | `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py tests/ops/test_live_proof.py -q` | ✅ |
| SMTP-19-02 | Preflight distinguishes blocking SMTP failures from non-blocking approval-link reachability failures | ops/unit | `PYTHONPATH=. pytest tests/ops/test_live_proof.py -q` | ✅ |
| SMTP-19-03 | Docs/result template record delivered recipient, rendered approval host, and skipped callback status clearly | docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ |
| SMTP-19-04 | SMTP transport mode is handled or diagnosed clearly for supported providers | unit | `PYTHONPATH=. pytest tests/services/test_mail_provider.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/ops/test_operational_docs.py -q`
- **Per wave merge:** `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py tests/ops/test_live_proof.py tests/ops/test_operational_docs.py -q`
- **Phase gate:** `PYTHONPATH=. pytest -q` plus one documented SMTP proof run

### Wave 0 Gaps

- [ ] `tests/services/test_mail_provider.py` — cover STARTTLS-on-587, implicit-TLS-on-465, and unsupported/misconfigured SMTP mode handling
- [ ] Extend `tests/ops/test_live_proof.py` — assert split preflight status, non-blocking approval reachability, and any new proof-state fields
- [ ] Extend `tests/ops/test_operational_docs.py` — assert the new Phase 19 runbook/result template or updated README link target
- [ ] Decide whether live-proof command surface stays `app.ops.live_proof` or moves to a new Phase 19-specific ops module before writing tests

## Sources

### Primary (HIGH confidence)

- Repository code: `app/services/mail_provider.py`, `app/ops/live_proof.py`, `app/graph/workflow.py`, `app/api/routes.py`, `tests/ops/test_live_proof.py`, `tests/ops/test_operational_docs.py`
- Python `smtplib` docs - https://docs.python.org/3/library/smtplib.html - checked `SMTP`, `SMTP_SSL`, and `starttls()` behavior
- Python `email.message` docs - https://docs.python.org/3/library/email.message.html - checked `EmailMessage`, `set_content()`, and `add_alternative()`
- PyPI FastAPI - https://pypi.org/project/fastapi/
- PyPI SQLAlchemy - https://pypi.org/project/SQLAlchemy/
- PyPI pydantic-settings - https://pypi.org/project/pydantic-settings/
- PyPI httpx - https://pypi.org/project/httpx/
- PyPI Uvicorn - https://pypi.org/project/uvicorn/
- PyPI psycopg - https://pypi.org/project/psycopg/
- PyPI Jinja2 - https://pypi.org/project/Jinja2/
- PyPI pytest - https://pypi.org/project/pytest/

### Secondary (MEDIUM confidence)

- Phase 15 research and runbook in `.planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/`
- `README.md` go-live and live-proof guidance

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - current versions were verified from PyPI and the SMTP/email behavior was checked against official Python docs
- Architecture: HIGH - recommendations are derived directly from current repo code and current Phase 15 operational coupling
- Pitfalls: HIGH - the transport-mode risk and proof-contract coupling are both evidenced by current code and docs

**Research date:** 2026-04-03
**Valid until:** 2026-05-03
