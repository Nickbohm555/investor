---
phase: 3
slug: scheduling-and-email-delivery
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-31
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/services/test_email.py tests/services/test_tokens.py tests/api/test_routes.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/services/test_email.py tests/services/test_tokens.py tests/api/test_routes.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | SCHD-02 | integration | `pytest tests/api/test_scheduling.py::test_duplicate_scheduled_trigger_does_not_create_second_primary_run -q` | ✅ seeded in task | ⬜ pending |
| 03-01-02 | 01 | 1 | SCHD-01 | smoke | `pytest tests/ops/test_cron_scripts.py::test_install_remove_status_cycle -q` | ✅ seeded in task | ⬜ pending |
| 03-01-03 | 01 | 1 | SCHD-03 | integration | `pytest tests/ops/test_cron_scripts.py::test_trigger_wrapper_loads_env_and_logs -q` | ✅ seeded in task | ⬜ pending |
| 03-02-01 | 02 | 2 | MAIL-01 | unit | `pytest tests/services/test_mail_provider.py::test_smtp_provider_sends_emailmessage -q` | ✅ seeded in task | ⬜ pending |
| 03-02-02 | 02 | 2 | MAIL-02 | unit | `pytest tests/services/test_email.py::test_renderer_supports_ranked_watchlist_and_no_action_paths -q` | ✅ expand existing | ⬜ pending |
| 03-02-03 | 02 | 2 | MAIL-03 | unit/integration | `pytest tests/services/test_tokens.py tests/api/test_routes.py -q` | ✅ expand existing | ⬜ pending |
| 03-03-01 | 03 | 3 | SCHD-02 | integration | `pytest tests/api/test_scheduling.py tests/api/test_routes.py -q` | ✅ available after plans 01-02 | ⬜ pending |
| 03-03-02 | 03 | 3 | MAIL-01 | integration | `pytest tests/services/test_mail_provider.py tests/services/test_email.py tests/api/test_routes.py -q` | ✅ available after plans 01-02 | ⬜ pending |
| 03-03-03 | 03 | 3 | SCHD-03 | integration | `pytest tests/ops/test_cron_scripts.py tests/api/test_scheduling.py tests/api/test_routes.py -q` | ✅ available after plans 01-02 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing plan tasks seed `tests/ops/test_cron_scripts.py` during `03-01` and expand it again during `03-03`
- [x] Existing plan tasks seed `tests/api/test_scheduling.py` during `03-01` and reuse it in `03-03`
- [x] Existing plan tasks seed `tests/services/test_mail_provider.py` during `03-02`
- [x] Existing plan tasks expand `tests/services/test_email.py` for ranked, watchlist, and no-action rendering during `03-02`
- [x] Existing plan tasks expand `tests/services/test_tokens.py` and `tests/api/test_routes.py` for external-base-url and expiry/run-scope coverage during `03-02` and `03-03`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Install the repo-managed cron job on the operator machine and confirm the crontab contains exactly one investor-managed block | SCHD-01 | Crontab behavior varies by host OS and user environment, so a real machine install should be spot-checked | Run the install script, inspect `crontab -l`, rerun install to confirm it stays single-entry, then run the remove script and confirm the managed block is gone |
| Trigger a scheduled run from cron with the real `.env` file and inspect the emitted log file for timestamps and trigger outcome | SCHD-03 | Cron uses a minimal shell environment that the automated suite cannot fully replicate | Install the cron job or run the wrapper directly under `/bin/sh`, verify it loads repo env values, and confirm success and failure cases append clear log lines |
| Send a real SMTP message against the chosen provider or relay and open the email to verify approval/rejection links resolve to the configured public base URL | MAIL-01, MAIL-02, MAIL-03 | End-to-end SMTP delivery and inbox rendering depend on external mail infrastructure and client behavior | Configure SMTP env vars, trigger a run, open the received message, verify subject/body content for the memo mode, and click both links to confirm they hit the intended external host |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 coverage is embedded in the first test-seeding tasks of Plans 01 and 02
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-31
