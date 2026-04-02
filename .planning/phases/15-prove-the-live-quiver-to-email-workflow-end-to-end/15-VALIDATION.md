---
phase: 15
slug: prove-the-live-quiver-to-email-workflow-end-to-end
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none |
| **Quick run command** | `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q` |
| **Full suite command** | `PYTHONPATH=. pytest -q` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q`
- **After every plan wave:** Run `PYTHONPATH=. pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green and one documented live proof run must be completed
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 0 | LQE-01 | integration + manual live proof | `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py -q` | ✅ | ⬜ pending |
| 15-01-02 | 01 | 0 | LQE-02 | integration + manual live proof | `PYTHONPATH=. pytest tests/integration/test_scheduled_submission_flow.py -q` | ✅ | ⬜ pending |
| 15-01-03 | 01 | 0 | LQE-03 | ops/docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Add a live-proof preflight script or documented commands for Quiver endpoint auth/status validation.
- [ ] Add a live-proof preflight script or documented commands for OpenAI-compatible tool-calling validation.
- [ ] Add a documented SMTP/inbox verification step before the integrated proof run.
- [ ] Add a persisted-state inspection command or script for `runs`, `approval_events`, and `state_transitions` by `run_id`.
- [ ] Add explicit docs for how `INVESTOR_EXTERNAL_BASE_URL` is made publicly reachable in the proof environment.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Delivered memo reaches `INVESTOR_DAILY_MEMO_TO_EMAIL` in the target operator inbox | LQE-01 | SMTP delivery and inbox acceptance require a real mail account | Start the configured runtime, trigger `POST /runs/trigger/scheduled`, and confirm the live memo arrives in `nickbohm555@gmail.com` with the expected rendered content. |
| Approval link resolves from the delivered email against `INVESTOR_EXTERNAL_BASE_URL` and updates persisted run state | LQE-02 | Public callback reachability and token handling require a real externally reachable app instance | Open the delivered approval link, confirm the callback reaches the app, then inspect `runs`, `approval_events`, and `state_transitions` for the target `run_id`. |
| Runbook records exact commands, observed logs, failure modes, and remaining manual steps after the proof | LQE-03 | The artifact is operator-facing documentation, not just code behavior | Follow the final runbook and confirm it includes trigger command, log markers, inbox verification, approval callback check, and explicit recovery guidance. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
