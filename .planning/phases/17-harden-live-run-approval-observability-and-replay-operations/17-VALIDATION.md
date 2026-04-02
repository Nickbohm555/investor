---
phase: 17
slug: harden-live-run-approval-observability-and-replay-operations
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-02
---

# Phase 17 — Validation Strategy

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

- **After every task commit:** Run `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py tests/ops/test_operational_docs.py -q` plus any new phase-specific test files created by that task.
- **After every plan wave:** Run `PYTHONPATH=. pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green, docs assets present, and one replay or re-drive proof path must be exercised against persisted run lineage.
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-00-01 | W0 | 0 | OPS-01, OPS-02, OPS-03 | TDD scaffolding | `test -f tests/ops/test_live_run_ops.py && test -f tests/integration/test_replay_flow.py` | ❌ W0 | ⬜ pending |
| 17-01-01 | 01 | 1 | OPS-01 | integration + repository | `PYTHONPATH=. pytest tests/integration/test_run_observability.py tests/api/test_scheduling.py -q` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 2 | OPS-02 | ops + integration | `PYTHONPATH=. pytest tests/ops/test_live_run_ops.py tests/integration/test_replay_flow.py -q` | ❌ W0 | ⬜ pending |
| 17-03-01 | 03 | 3 | OPS-03 | ops + docs | `PYTHONPATH=. pytest tests/ops/test_live_run_ops.py tests/ops/test_operational_docs.py -q` | ❌ W0 | ⬜ pending |
| 17-04-01 | 04 | 4 | ARCH-OPS-04 | docs drift | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ops/test_live_run_ops.py` — covers the repo-owned inspect, replay, and re-drive operator surface with side-effect guards.
- [ ] `tests/integration/test_replay_flow.py` — proves linked-run lineage, evidence reuse, and no-default side effects.
- [ ] `tests/integration/test_run_observability.py` — proves provider/stage failures are queryable from persisted records and aligned logs.
- [ ] Existing infrastructure covers pytest and DB-backed test execution; no framework install is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A live operator can inspect a failed or successful run and clearly distinguish Quiver, LLM, SMTP, approval-link, and broker-side outcomes from repo-owned tooling plus persisted records. | OPS-01 | Real provider failures and live credentials cannot be fully reproduced in CI. | Trigger or inspect a real run, then verify the operator surface and persisted event history show stage, provider, outcome, and run lineage without ad hoc SQL or code spelunking. |
| A chosen run can be replayed or re-driven safely as a new linked run with preserved evidence and trace context, while email and broker actions stay disabled unless explicitly enabled. | OPS-02 | Safe replay versus live re-drive behavior depends on real runtime settings and operator intent. | Execute the replay or re-drive command for a known `run_id`, verify the new run has `replay_of_run_id` set, confirm preserved evidence metadata is present, and confirm no email or broker side effects occur unless the explicit enable flags were provided. |
| Secrets, callback hosts, and runbook steps are safe for repeated live-credential iteration. | OPS-03 | Secret redaction and delivery-path safety need human review against real env values and docs. | Review CLI output, logs, and docs artifacts to confirm sensitive values are masked, the configured external approval host is explicit, and the runbook includes failure recovery for misrouting or provider outages. |
| The Quiver research-flow Excalidraw, exported screenshot, and README explanation stay aligned with the actual four live endpoints and their purpose. | ARCH-OPS-04 | Visual clarity and asset linkage require human review in addition to docs drift checks. | Open the Excalidraw and screenshot, confirm the README references the screenshot, and verify the diagram explains `/beta/live/congresstrading`, `/beta/live/insiders`, `/beta/live/govcontracts`, and `/beta/live/lobbying` plus why each call exists. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
