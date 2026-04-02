---
phase: 13
slug: replace-host-cron-scripts-with-a-docker-native-scheduler
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-02
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 7.1.2` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py -q`
- **After every plan wave:** Run `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/ops/test_operational_docs.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 0 | TBD-13-01 | ops/integration | `python -m pytest tests/ops/test_docker_scheduler.py -q` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 0 | TBD-13-03 | ops | `python -m pytest tests/ops/test_docker_scheduler.py tests/ops/test_operational_docs.py -q` | ❌ W0 | ⬜ pending |
| 13-02-01 | 02 | 1 | TBD-13-01 | ops/integration | `python -m pytest tests/ops/test_docker_scheduler.py -q` | ❌ W0 | ⬜ pending |
| 13-02-02 | 02 | 1 | TBD-13-02 | api/integration | `python -m pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q` | ❌ W0 | ⬜ pending |
| 13-03-01 | 03 | 2 | TBD-13-03 | ops/docs | `python -m pytest tests/ops/test_docker_scheduler.py tests/ops/test_operational_docs.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `Dockerfile` — app container build does not exist yet
- [ ] `.dockerignore` — build context guard does not exist yet
- [ ] `ops/scheduler/crontab` — repo-owned schedule contract file is missing
- [ ] `ops/scheduler/trigger-scheduled.sh` — scheduler entrypoint wrapper is missing
- [ ] `tests/ops/test_docker_scheduler.py` — Compose and scheduler contract coverage is missing
- [ ] `tests/api/test_scheduling.py` — source file is absent from the current workspace
- [ ] `tests/ops/test_cron_scripts.py` — source file is absent from the current workspace

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scheduler container calls the live scheduled route after stack startup | TBD-13-01 | Requires observing real Compose startup ordering and service logs | Run `docker compose up -d --build`, then `docker compose logs --no-color scheduler app | tail -n 100` and confirm one scheduler job hits `/runs/trigger/scheduled` successfully without host cron. |
| Compose-native operator path replaces host cron as the primary runtime contract | TBD-13-03 | Requires validating docs and runtime flow together | Follow the Phase 13 README instructions on a clean checkout and confirm the operator uses `docker compose` commands instead of `./scripts/cron-install.sh` for the default scheduled path. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
