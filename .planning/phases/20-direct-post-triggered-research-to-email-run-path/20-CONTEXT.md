# Phase 20: Direct POST-triggered research-to-email run path - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase should prove and harden the narrowest live operator path that matters right now: one direct manual POST request starts a run, the existing research agent executes, and one real email is delivered to the configured inbox.

The scope anchor is intentionally narrower than the scheduler and approval work:
- Use a direct trigger, not cron or the scheduled-trigger workflow.
- Reuse the existing research-agent and email-delivery path instead of inventing a second research or mail subsystem.
- Stop at delivered email for this phase.

Out of scope for this phase:
- Cron and scheduler behavior
- Approval callback execution
- Broker execution or post-approval flows
- Any new UI or dashboard work
</domain>

<decisions>
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
</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants to focus on "just do post call -> research agent -> email now".
- This phase should help bypass the current cognitive overhead of cron and broader live-proof contracts while env values are still being corrected.
- The current investigation showed that preflight fails before SMTP when `INVESTOR_QUIVER_BASE_URL` falls back to the placeholder default, so planning should not assume the inbox address is the first issue.
- Quotes in `.env` are optional for most values; normal full URLs should be used directly.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Trigger and runtime flow
- `app/api/routes.py` — defines the direct manual `POST /runs/trigger` route and the separate scheduled-trigger route that this phase should avoid centering.
- `app/runtime.py` — shows the existing runtime composition for Quiver, research LLM, workflow engine, and mail provider.
- `app/graph/workflow.py` — shows the current research-to-email flow and where the approval-link URLs are rendered into the outgoing memo.

### Operational proof and env requirements
- `.planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RUNBOOK.md` — current SMTP-only live-proof contract; useful as a reference but broader than this phase.
- `.planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RESULT.md` — records the exact live blockers encountered before SMTP delivery.
- `app/ops/live_proof.py` — current preflight, trigger, and inspect helpers; important because it currently checks Quiver and LLM before SMTP.
- `app/config.py` — documents the default env fallbacks that caused confusion during live setup.

### Existing proof harnesses
- `app/ops/dry_run.py` — reusable proof shape for one trigger through one delivered memo with stable doubles; likely the closest existing model for a reduced live path.
- `tests/integration/test_scheduled_submission_flow.py` — proves the current route-to-email lifecycle in tests and shows what reuse already exists.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/api/routes.py::trigger_run` — already creates a manual run with `trigger_source="manual"` and starts the workflow engine directly.
- `app/runtime.py::build_runtime` — already wires the real `ResearchNode`, `HttpResearchLLM`, `QuiverClient`, and `SmtpMailProvider`.
- `app/graph/workflow.py::invoke` — already performs the exact path this phase wants: build evidence bundles, run research, compose the report email, and send it.
- `app/ops/dry_run.py` — already demonstrates a compact operator-proof pattern and a reusable env override shape.

### Established Patterns
- The repo already separates manual trigger and scheduled trigger routes. Phase 20 should not blur them back together.
- Email sending is already behind `mail_provider.send(...)`; Phase 20 should preserve that seam.
- Approval links are still rendered in the email from `external_base_url`, even if callback execution is not part of this phase's success criteria.
- Current live-proof tooling is ordered so Quiver and LLM checks happen before SMTP inspection. Any proof workflow that claims "email first" has to account for that reality.

### Integration Points
- Direct trigger entrypoint: `POST /runs/trigger`
- Workflow execution seam: `runtime.workflow_engine.start_run(...)`
- Mail delivery seam: `SmtpMailProvider.send(...)`
- Live diagnostics seam: `python -m app.ops.live_proof preflight`
</code_context>

<deferred>
## Deferred Ideas

- Reintroducing cron and scheduled-trigger proof to this narrower live path
- Approval callback verification or replay work
- Broker execution confirmation or live order submission
- Broader operational cleanup beyond what is necessary to get one manual POST-triggered email out
</deferred>

---

*Phase: 20-direct-post-triggered-research-to-email-run-path*
*Context gathered: 2026-04-03*
