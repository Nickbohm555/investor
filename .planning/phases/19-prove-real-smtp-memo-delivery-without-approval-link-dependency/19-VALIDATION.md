---
phase: 19
slug: prove-real-smtp-memo-delivery-without-approval-link-dependency
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-03
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/services/test_mail_provider.py -q` |
| **Full suite command** | `PYTHONPATH=. pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/services/test_mail_provider.py -q`
- **After every plan wave:** Run `PYTHONPATH=. pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | SMTP-19-02, SMTP-19-04 | ops/unit | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/services/test_mail_provider.py -q` | ✅ | ⬜ pending |
| 19-01-02 | 01 | 1 | SMTP-19-02, SMTP-19-04 | ops/unit | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/services/test_mail_provider.py -q` | ✅ | ⬜ pending |
| 19-02-01 | 02 | 2 | SMTP-19-01, SMTP-19-03 | docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |
| 19-02-02 | 02 | 2 | SMTP-19-01, SMTP-19-03 | docs | `PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |
| 19-03-01 | 03 | 3 | SMTP-19-01 | integration + artifact | `PYTHONPATH=. pytest tests/ops/test_live_proof.py tests/ops/test_operational_docs.py tests/services/test_mail_provider.py -q && rg -n "^run_id:|^scheduled_trigger_status:|^smtp_ready:|^approval_reachability_ready:|^blocking_failures:|^warnings:|^scheduled_trigger_log_line:|^memo_delivery_log_line:|^current_step:|^approval_status:|^final_run_status:" .planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RESULT.md && rg -n "skipped-for-phase-19|memo_delivery result=|scheduled_trigger result=" .planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RESULT.md` | ✅ | ⬜ pending |
| 19-03-02 | 03 | 3 | SMTP-19-01 | checkpoint/manual | `printf "checkpoint: waiting for human inbox verification\n"` | ✅ | ⬜ pending |
| 19-03-03 | 03 | 3 | SMTP-19-01 | artifact + docs | `rg -n "^memo_delivered_to:|^approval_link_host:|^approval_callback_status: skipped-for-phase-19|^final_run_status:" .planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RESULT.md && rg -n "remaining_manual_steps:" .planning/phases/19-prove-real-smtp-memo-delivery-without-approval-link-dependency/19-LIVE-PROOF-RESULT.md && PYTHONPATH=. pytest tests/ops/test_operational_docs.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_mail_provider.py` — cover STARTTLS-on-587, implicit-TLS-on-465, and unsupported/misconfigured SMTP mode handling
- [ ] `tests/ops/test_live_proof.py` — extend split preflight status, non-blocking approval reachability, and proof-state assertions
- [ ] `tests/ops/test_operational_docs.py` — lock the Phase 19 SMTP-proof runbook/result-template contract

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Delivered memo reaches the target inbox and shows the rendered approval host | SMTP-19-01, SMTP-19-03 | Real inbox delivery and rendered email content cannot be fully proven in CI | Start the runtime, run `python -m app.ops.live_proof preflight`, run `python -m app.ops.live_proof trigger-scheduled`, confirm delivery to `INVESTOR_DAILY_MEMO_TO_EMAIL`, and record `run_id`, recipient, rendered approval-link host, and observed `memo_delivery result=sent` evidence in the Phase 19 proof artifact |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
