---
phase: 11
slug: scheduling-reliability-and-end-to-end-execution-proof
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-31
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.1.2 installed in repo environment; latest available 9.0.2 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_operational_docs.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~75 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `<automated>` command from the active plan
- **After every plan wave:** Run `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_operational_docs.py tests/api/test_execution_confirmation.py tests/ops/test_dry_run.py tests/integration/test_scheduled_submission_flow.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 75 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | SC11-01 | ops/docs | `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_operational_docs.py -q` | ✅ partial | ⬜ pending |
| 11-01-02 | 01 | 1 | SC11-01 | ops/docs | `python -m pytest tests/ops/test_cron_scripts.py tests/ops/test_operational_docs.py -q` | ✅ partial | ⬜ pending |
| 11-02-01 | 02 | 1 | SC11-02 | api/ops | `python -m pytest tests/api/test_execution_confirmation.py tests/tools/test_alpaca_orders.py tests/ops/test_dry_run.py -q` | ❌ Wave 0 | ⬜ pending |
| 11-02-02 | 02 | 1 | SC11-02 | api/ops | `python -m pytest tests/api/test_execution_confirmation.py tests/tools/test_alpaca_orders.py tests/ops/test_dry_run.py -q` | ❌ Wave 0 | ⬜ pending |
| 11-03-01 | 03 | 2 | SC11-02 | integration | `python -m pytest tests/integration/test_scheduled_submission_flow.py -q` | ❌ Wave 0 | ⬜ pending |
| 11-03-02 | 03 | 2 | SC11-03 | integration | `python -m pytest tests/integration/test_scheduled_submission_flow.py tests/api/test_execution_confirmation.py tests/ops/test_dry_run.py -q` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/integration/test_scheduled_submission_flow.py` — scheduled trigger to memo to approval to confirmation to submit
- [ ] `tests/api/test_execution_confirmation.py` — explicit confirmation endpoint semantics and duplicate/stale handling
- [ ] `tests/tools/test_alpaca_orders.py` — Alpaca order submission adapter and status parsing
- [ ] `app/ops/dry_run.py` update — JSON output must include submitted-order proof, not only `broker_prestaged`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Installed cron fires at the intended local wall-clock time on the operator host | SC11-01 | Repo tests can verify generated crontab text, but not the host cron daemon's real execution behavior or timezone configuration | Install the managed cron block with `./scripts/cron-install.sh`, inspect `crontab -l`, confirm the installed expression and any `CRON_TZ=America/New_York` line match the documented 7:00am ET path, then verify a real scheduled invocation writes to `logs/cron/daily-trigger.log` at the expected time |
| Real Alpaca paper credentials are available if the operator wants a non-mocked paper-trading smoke after automated verification | SC11-02 | The automated plan uses doubles for determinism; one optional real-paper smoke remains useful before live consideration | After automated tests pass, run the repo-local execution flow with paper credentials and verify the returned client order IDs match the persisted `submitted_orders` payload |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 75s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
