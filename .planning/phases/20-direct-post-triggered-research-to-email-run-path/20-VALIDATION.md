---
phase: 20
slug: direct-post-triggered-research-to-email-run-path
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 7.1.2` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/ops/test_live_proof.py -q` plus any new Phase 20 test files touched by the task |
| **Full suite command** | `PYTHONPATH=. pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=. pytest tests/api/test_scheduling.py tests/ops/test_live_proof.py -q` plus the new Phase 20 test files touched by the task
- **After every plan wave:** Run `PYTHONPATH=. pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | PH20-01 | api/integration | `PYTHONPATH=. pytest tests/api/test_manual_trigger.py tests/integration/test_manual_trigger_email_flow.py -q` | ✅ | ✅ green |
| 20-02-01 | 02 | 1 | PH20-02 | ops/unit | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/ops/test_manual_post_proof.py -q` | ✅ | ✅ green |
| 20-03-01 | 03 | 2 | PH20-03 | docs/assertion | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/api/test_manual_trigger.py` — stubs for PH20-01
- [x] `tests/integration/test_manual_trigger_email_flow.py` — stubs for PH20-01
- [x] `tests/ops/test_manual_post_proof.py` — stubs for PH20-02
- [x] `PYTHONPATH=.` in repo test commands — avoid `ModuleNotFoundError: No module named 'app'`

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live operator can run one direct `POST /runs/trigger` against the real environment and receive one delivered memo email | PH20-01 | Requires real Quiver, LLM, SMTP, runtime env values, and inbox delivery outside test doubles | Start the app with live env values, run the Phase 20 manual-proof helper or documented POST flow once, confirm the response includes a run id, inspect persisted run state, and verify the configured inbox received the memo |
| Preflight output names the first blocking live dependency in operator order when env values are missing or placeholder | PH20-02 | Requires intentionally misconfigured live env values and observation of operator-facing diagnostics | Run the Phase 20 preflight command with one required env value unset or placeholder, confirm output names the exact missing or placeholder setting before attempting a live run |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete
