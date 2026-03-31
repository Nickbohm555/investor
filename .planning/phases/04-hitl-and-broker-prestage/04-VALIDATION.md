---
phase: 4
slug: hitl-and-broker-prestage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | HITL-01 | integration | `python -m pytest tests/integration/test_hitl_resume.py::test_approval_resumes_same_thread -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | HITL-02 | integration | `python -m pytest tests/integration/test_hitl_resume.py::test_reject_finalizes_without_broker_side_effects -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | BRKR-01 | integration | `python -m pytest tests/integration/test_broker_prestage.py::test_approved_run_creates_broker_artifacts -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | BRKR-02 | unit + integration | `python -m pytest tests/services/test_broker_policy.py tests/integration/test_broker_prestage.py -q` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 1 | BRKR-03 | integration | `python -m pytest tests/integration/test_broker_prestage.py::test_broker_artifact_links_to_run_and_recommendations -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/integration/test_hitl_resume.py` — durable approve/reject/duplicate/stale coverage for HITL-01 and HITL-02
- [ ] `tests/integration/test_broker_prestage.py` — end-to-end approval-to-artifact coverage for BRKR-01 through BRKR-03
- [ ] `tests/services/test_broker_policy.py` — deterministic policy checks for buying power, asset support, and order shape
- [ ] `tests/conftest.py` or equivalent shared fixture module — persisted run state, recommendations, and mocked Alpaca account/asset responses

*Existing infrastructure covers the framework and config baseline, but this phase still needs Wave 0 test files and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Approval link opened from a real email resumes or rejects the expected run in operator-visible flow | HITL-01, HITL-02 | End-to-end email client interaction and operator confirmation path are outside the current automated boundary | Start the app with persisted storage, trigger a run, use the emailed approve and reject links, verify the run transitions correctly, and confirm reject leaves no broker artifact |
| Paper and live broker configuration are visibly separated in operational setup | BRKR-02 | Requires environment-level validation across distinct credential/base URL combinations | Start once with paper config and once with live config, inspect startup diagnostics and created artifacts, and verify the recorded broker mode matches the selected environment |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
