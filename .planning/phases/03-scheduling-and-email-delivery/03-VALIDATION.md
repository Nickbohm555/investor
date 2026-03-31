---
phase: 3
slug: scheduling-and-email-delivery
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 03-01-01 | 01 | 0 | SCHD-01 | smoke | `pytest tests/ops/test_cron_scripts.py::test_install_remove_status_cycle -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | SCHD-02 | integration | `pytest tests/api/test_scheduling.py::test_duplicate_scheduled_trigger_does_not_create_second_primary_run -q` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | SCHD-03 | integration | `pytest tests/ops/test_cron_scripts.py::test_trigger_wrapper_loads_env_and_logs -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 0 | MAIL-01 | unit | `pytest tests/services/test_mail_provider.py::test_smtp_provider_sends_emailmessage -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | MAIL-02 | unit | `pytest tests/services/test_email.py::test_renderer_supports_ranked_watchlist_and_no_action_paths -q` | ✅ expand | ⬜ pending |
| 03-02-03 | 02 | 1 | MAIL-03 | unit/integration | `pytest tests/services/test_tokens.py tests/api/test_routes.py -q` | ✅ partial | ⬜ pending |
| 03-03-01 | 03 | 2 | SCHD-02 | integration | `pytest tests/api/test_scheduling.py tests/api/test_routes.py -q` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | MAIL-01 | integration | `pytest tests/services/test_mail_provider.py tests/services/test_email.py tests/api/test_routes.py -q` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 2 | SCHD-03 | integration | `pytest tests/ops/test_cron_scripts.py tests/api/test_scheduling.py tests/api/test_routes.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ops/test_cron_scripts.py` — add cron install/remove/status and trigger-wrapper coverage for `SCHD-01` and `SCHD-03`
- [ ] `tests/api/test_scheduling.py` — add scheduled-trigger idempotency coverage for `SCHD-02`
- [ ] `tests/services/test_mail_provider.py` — add SMTP provider contract coverage for `MAIL-01`
- [ ] Expand `tests/services/test_email.py` — add ranked, watchlist, and no-action memo rendering coverage for `MAIL-02`
- [ ] Expand `tests/services/test_tokens.py` and `tests/api/test_routes.py` — add external-base-url and expiry/run-scope coverage for `MAIL-03`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Install the repo-managed cron job on the operator machine and confirm the crontab contains exactly one investor-managed block | SCHD-01 | Crontab behavior varies by host OS and user environment, so a real machine install should be spot-checked | Run the install script, inspect `crontab -l`, rerun install to confirm it stays single-entry, then run the remove script and confirm the managed block is gone |
| Trigger a scheduled run from cron with the real `.env` file and inspect the emitted log file for timestamps and trigger outcome | SCHD-03 | Cron uses a minimal shell environment that the automated suite cannot fully replicate | Install the cron job or run the wrapper directly under `/bin/sh`, verify it loads repo env values, and confirm success and failure cases append clear log lines |
| Send a real SMTP message against the chosen provider or relay and open the email to verify approval/rejection links resolve to the configured public base URL | MAIL-01, MAIL-02, MAIL-03 | End-to-end SMTP delivery and inbox rendering depend on external mail infrastructure and client behavior | Configure SMTP env vars, trigger a run, open the received message, verify subject/body content for the memo mode, and click both links to confirm they hit the intended external host |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
