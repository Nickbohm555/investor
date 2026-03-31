---
phase: 05
slug: operational-readiness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.2` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~20-25 seconds for quick checks; full suite unchanged |

---

## Sampling Rate

- **After 05-01 Task 1 commit:** Run `python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/api/test_routes.py -q`
- **After 05-01 Task 2 commit:** Run `python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/ops/test_dry_run.py -q`
- **After 05-02 Task 1 or Task 2 commit:** Run `python -m pytest tests/ops/test_operational_docs.py -q`
- **After every plan wave:** Run `python -m pytest tests/api/test_routes.py tests/api/test_scheduling.py tests/ops/test_cron_scripts.py tests/integration/test_broker_prestage.py tests/ops/test_readiness.py tests/services/test_research_llm.py tests/ops/test_dry_run.py tests/ops/test_operational_docs.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | OPER-01 | unit/integration | `python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/api/test_routes.py -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | OPER-02 | integration/smoke | `python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/ops/test_dry_run.py -q` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | OPER-03 | doc/assertion | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ops/test_readiness.py` — startup validation, placeholder detection, and rendered diagnostics for `OPER-01`
- [ ] `tests/services/test_research_llm.py` — env-backed research adapter and normal app-composition coverage proving `StaticLLM` and default static Quiver transport are gone
- [ ] `tests/ops/test_dry_run.py` — deterministic end-to-end dry-run covering trigger through approval and prestage for `OPER-02`
- [ ] `tests/ops/test_operational_docs.py` — asserts required env keys and README checklist content for `OPER-03`
- [ ] `tests/conftest.py` — shared dry-run fixtures for local mail capture and adapter transports if existing doubles are insufficient

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | None | All phase behaviors should be automated through the readiness, dry-run, and docs assertions above | None |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
