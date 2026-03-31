---
phase: 4
slug: hitl-and-broker-prestage
status: ready
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py tests/services/test_persistence.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task's exact `<automated>` command from the map below.
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | HITL-01 | integration | `python -m pytest tests/integration/test_hitl_resume.py -q` | task-owned | ⬜ pending |
| 04-01-02 | 01 | 1 | HITL-02 | route + workflow + integration | `python -m pytest tests/api/test_routes.py tests/graph/test_workflow.py tests/integration/test_hitl_resume.py -q` | task-owned | ⬜ pending |
| 04-02-01 | 02 | 1 | BRKR-01, BRKR-03 | persistence | `python -m pytest tests/services/test_persistence.py -q` | task-owned | ⬜ pending |
| 04-02-02 | 02 | 1 | BRKR-02 | unit + client | `python -m pytest tests/services/test_broker_policy.py tests/tools/test_clients.py -q` | task-owned | ⬜ pending |
| 04-03-01 | 03 | 2 | HITL-01, HITL-02 | route | `python -m pytest tests/api/test_routes.py -q` | task-owned | ⬜ pending |
| 04-03-02 | 03 | 2 | BRKR-01, BRKR-02, BRKR-03 | integration | `python -m pytest tests/integration/test_hitl_resume.py tests/integration/test_broker_prestage.py tests/api/test_routes.py -q` | task-owned | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers this phase. Test files and fixtures are created by their owning tasks during normal execution, so there is no separate Wave 0 plan for Phase 4.

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
- [x] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 25s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-31
