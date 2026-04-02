---
phase: 15
slug: prove-the-live-quiver-to-email-workflow-end-to-end
status: planned
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_live_proof.py tests/ops/test_operational_docs.py -q` |
| **Full suite command** | `PYTHONPATH=. pytest -q` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_live_proof.py tests/ops/test_operational_docs.py -q`
- **After every plan wave:** Run `PYTHONPATH=. pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green and one documented live proof run must be completed
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | LQE-01, LQE-02 | ops/TDD | `PYTHONPATH=. pytest tests/ops/test_live_proof.py -q` | ✅ | ⬜ pending |
| 15-01-02 | 01 | 1 | LQE-01, LQE-02 | ops/TDD | `PYTHONPATH=. pytest tests/ops/test_live_proof.py -q` | ✅ | ⬜ pending |
| 15-02-01 | 02 | 2 | LQE-03 | docs/TDD | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |
| 15-02-02 | 02 | 2 | LQE-03 | docs/TDD | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |
| 15-03-01 | 03 | 3 | LQE-01, LQE-02 | live ops + manual proof | `python -m app.ops.live_proof preflight && python -m app.ops.live_proof trigger-scheduled` | ✅ | ⬜ pending |
| 15-03-02 | 03 | 3 | LQE-01, LQE-02 | checkpoint/manual | `rg -n "^memo_delivered_to: |^approval_callback_status: |^approval_link_host: " .planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-LIVE-PROOF-RESULT.md` | ✅ | ⬜ pending |
| 15-03-03 | 03 | 3 | LQE-01, LQE-02, LQE-03 | live ops + persisted verification | `RUN_ID=$(rg -o "run-[A-Za-z0-9-]+" .planning/phases/15-prove-the-live-quiver-to-email-workflow-end-to-end/15-LIVE-PROOF-RESULT.md -m1); python -m app.ops.live_proof inspect-run --run-id "$RUN_ID" && docker compose logs --no-color app | rg "scheduled_trigger result=|memo_delivery result="` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Plan Coverage Summary

- [x] **Plan 15-01 / Wave 1:** Adds the repo-owned live-proof CLI with Quiver, LLM, SMTP, and approval-boundary reachability preflight plus persisted run inspection.
- [x] **Plan 15-02 / Wave 2:** Locks the README entrypoint, Phase 15 runbook, and `15-LIVE-PROOF-RESULT.md` template to the required workflow and evidence fields.
- [x] **Plan 15-03 / Wave 3:** Executes the live proof, records inbox approval behavior, captures persisted callback fields, and stores observed scheduled-trigger and memo-delivery log lines.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Delivered memo reaches `INVESTOR_DAILY_MEMO_TO_EMAIL` in the target operator inbox | LQE-01 | SMTP delivery and inbox acceptance require a real mail account | Start the configured runtime, require a passing preflight reachability probe, trigger `POST /runs/trigger/scheduled`, and confirm the live memo arrives in `nickbohm555@gmail.com` with the expected rendered content. |
| Approval link resolves from the delivered email against `INVESTOR_EXTERNAL_BASE_URL` and updates persisted run state | LQE-02 | Public callback reachability and token handling require a real externally reachable app instance | Open the delivered approval link, confirm the callback reaches the app, then inspect `runs`, `approval_events`, and `state_transitions` for the target `run_id`, including persisted `current_step` and `approval_status`. |
| Runbook and result artifact record exact commands, observed logs, failure modes, and remaining manual steps after the proof | LQE-03 | The artifact is operator-facing documentation plus live evidence, not just code behavior | Follow the final runbook and confirm it includes the approval-boundary probe, trigger command, scheduled-trigger and memo-delivery log markers, inbox verification, approval callback check, persisted callback fields, and explicit recovery guidance. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] All tasks have `<automated>` verify commands aligned to the 3-plan Phase 15 breakdown
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Plan coverage summary matches Plans 15-01 through 15-03
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
