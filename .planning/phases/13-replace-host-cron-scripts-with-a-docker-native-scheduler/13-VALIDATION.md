---
phase: 13
slug: replace-host-cron-scripts-with-a-docker-native-scheduler
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-02
updated: 2026-04-02
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

- **After every task commit:** Run the task-level command from the verification map below
- **After Plan 01:** Run `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q`
- **After Plan 02:** Run `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q` and `docker compose config >/dev/null`
- **After Plan 03:** Run `python -m pytest tests/ops/test_operational_docs.py tests/ops/test_docker_scheduler.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | TBD-13-01 | api/integration | `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q` | ❌ W1 | ⬜ pending |
| 13-01-02 | 01 | 1 | TBD-13-01, TBD-13-02 | ops | `python -m pytest tests/ops/test_docker_scheduler.py -q` | ❌ W1 | ⬜ pending |
| 13-02-01 | 02 | 2 | TBD-13-01 | ops/integration | `python -m pytest tests/ops/test_docker_scheduler.py -q && docker compose config >/dev/null` | ❌ W1 | ⬜ pending |
| 13-02-02 | 02 | 2 | TBD-13-02 | api/integration | `python -m pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q` | ❌ W1 | ⬜ pending |
| 13-03-01 | 03 | 3 | TBD-13-03 | ops/docs | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ W3 | ⬜ pending |
| 13-03-02 | 03 | 3 | TBD-13-03 | ops/docs | `python -m pytest tests/ops/test_operational_docs.py tests/ops/test_docker_scheduler.py -q` | ❌ W3 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `Dockerfile` — app container build does not exist yet
- [ ] `.dockerignore` — build context guard does not exist yet
- [ ] `ops/docker/start-app-runtime.sh` — combined app-container runtime entrypoint is missing
- [ ] `ops/scheduler/crontab` — repo-owned schedule contract file is missing
- [ ] `ops/scheduler/start-supercronic.sh` — scheduler bootstrap script is missing
- [ ] `ops/scheduler/trigger-scheduled.sh` — scheduler trigger wrapper is missing
- [ ] `tests/ops/test_docker_scheduler.py` — Docker scheduler contract coverage is missing
- [ ] `tests/api/test_scheduling.py` — source file is absent from the current workspace
- [ ] `tests/integration/test_scheduled_submission_flow.py` — source file is absent from the current workspace

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App container starts both FastAPI and the repo-managed scheduler process after stack startup | TBD-13-01 | Requires observing real startup ordering and logs from the combined runtime | Run `docker compose up -d --build`, then `docker compose logs --no-color app | tail -n 100` and confirm the output shows the rendered Supercronic crontab plus a scheduler trigger result line without any separate `scheduler` service. |
| Docker-native operator path replaces host cron as the primary runtime contract | TBD-13-03 | Requires validating docs and runtime flow together | Follow the Phase 13 README instructions on a clean checkout and confirm the operator uses `docker compose up -d --build`, `docker compose logs -f migrate app`, and `docker compose down -v` instead of any `./scripts/cron-*.sh` workflow. |

---

## Validation Sign-Off

- [x] All 6 tasks have `<automated>` verify or intentional red-first validation
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Validation map matches revised waves 1 -> 2 -> 3
- [x] Stale references such as `tests/ops/test_cron_scripts.py` removed
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
