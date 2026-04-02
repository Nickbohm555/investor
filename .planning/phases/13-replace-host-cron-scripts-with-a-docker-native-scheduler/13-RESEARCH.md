# Phase 13: Replace Host Cron Scripts With A Docker-Native Scheduler - Research

**Researched:** 2026-04-02
**Domain:** Container-native scheduling for an existing FastAPI/Postgres workflow with an existing scheduled HTTP trigger seam
**Confidence:** HIGH

## User Constraints

No `*-CONTEXT.md` exists for Phase 13, so there are no phase-specific locked decisions copied from upstream discussion.

Repo constraints that still apply:
- Keep the existing Python/FastAPI/Postgres direction.
- Move scheduling off host `crontab` management and into a docker-native scheduler path.
- Keep the system local-first and single-operator friendly.
- Preserve the existing durable app-owned scheduling semantics rather than moving dedupe into shell or scheduler state.

Planning-relevant open decisions caused by the missing `CONTEXT.md`:
- Whether the operator-facing runtime should become `docker compose up -d` as the primary path, or whether bare-metal `uvicorn` remains documented alongside Compose.
- Whether host helper scripts should be removed entirely or retained as thin wrappers around Docker Compose commands.

## Summary

Phase 13 should not redesign scheduling logic. The repo already has the correct application seam: `POST /runs/trigger/scheduled` is token-guarded, ET schedule keys are computed in Python, and duplicate suppression is enforced in Postgres via `schedule_key`. The work to plan is operational migration: replace host-installed cron scripts with a Compose-managed scheduler container that calls the same HTTP route.

Docker Compose does not provide cron-style scheduling by itself. The clean path is therefore a three-service runtime: `postgres`, `app`, and `scheduler`, plus an explicit migration step. Use a dedicated scheduler container built around Supercronic, not host `crontab`, not a background loop inside the web container, and not a Docker-socket-driven label scheduler. Supercronic is designed for containers, keeps container env vars available to jobs, logs to `stdout`/`stderr`, handles signals cleanly, supports `TZ` and `CRON_TZ`, and already matches the repo's cron-style operator contract.

The largest planning trap is assuming this phase is just a `docker-compose.yml` edit. It is not. The repository currently has no `Dockerfile`, no `.dockerignore`, and no checked-in Python test source files under `tests/`; only compiled `.pyc` artifacts are present. Phase 13 therefore needs an explicit Wave 0 for container build/runtime assets and for restoring or recreating scheduler-related tests before implementation work can be trusted.

**Primary recommendation:** Build a dedicated `scheduler` Compose service that runs Supercronic against a repo-owned crontab file and `curl`s the existing scheduled-trigger endpoint on the internal Compose network; keep dedupe in the app/database path exactly as it works now.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docker Compose CLI | 2.40.3 (verified locally on 2026-04-02) | Run the multi-container local stack | The repo already uses Compose for Postgres, and current Compose supports `depends_on.condition: service_healthy`, `env_file`, healthchecks, and service DNS cleanly. |
| Supercronic | v0.2.43 (latest release visible on GitHub releases as of 2026-04-02) | Run cron-format schedules inside a dedicated scheduler container | It is explicitly designed for containers: env inheritance, stdout/stderr logging, graceful signal handling, `TZ`/`CRON_TZ`, and overlap warnings. |
| FastAPI scheduled trigger route | Existing repo app route | Stable execution seam for scheduled runs | Reusing the current HTTP trigger avoids inventing a second scheduler-only code path. |
| Postgres | 16 (current repo Compose image) | Persist run state and enforce schedule-key uniqueness | Scheduled dedupe already belongs here and should remain the source of truth. |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Alembic | Existing repo dependency | Run schema migrations before app/scheduler startup | Use a one-shot `migrate` service or equivalent entrypoint step so scheduled jobs never start against stale schema. |
| `curl` | Current distro package in scheduler image | Call `http://app:8000/runs/trigger/scheduled` from the scheduler job | Use for the scheduler command because the route already exists and returns explicit success/duplicate/failure semantics. |
| `tzdata` | Current distro package in app/scheduler images | Ensure `America/New_York` is present inside containers | Use in both app and scheduler images so ET schedule behavior is explicit and testable. |
| Docker healthchecks | Dockerfile/Compose feature | Gate service startup on Postgres and app readiness | Use with `depends_on.condition: service_healthy` so the scheduler does not fire before the API is actually ready. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Supercronic sidecar hitting HTTP | Ofelia v0.3.21 | Ofelia is viable, but it is Docker-socket-centric and label-driven; that adds Docker API access and configuration indirection the repo does not need for one stable HTTP trigger. |
| Separate scheduler service | Run cron inside the web container | Simpler image count, but it couples unrelated processes, weakens observability, and makes PID 1 / signal / restart behavior harder to reason about. |
| Existing scheduled HTTP route | Scheduler calling Python modules directly | Bypasses the repo's current auth, logging, duplicate-response, and operator-proof seams. |

**Installation / runtime target:**
```bash
docker compose up -d --build
docker compose logs -f app scheduler
```

**Version verification:**
- Docker Compose local version verified with `docker compose version` on 2026-04-02.
- Supercronic release version verified from GitHub releases page on 2026-04-02.
- Ofelia release version verified from GitHub releases page on 2026-04-02.

## Architecture Patterns

### Recommended Project Structure

```text
.
├── Dockerfile                 # app image
├── .dockerignore              # keep build context small
├── docker-compose.yml         # postgres + migrate + app + scheduler
├── ops/
│   └── scheduler/
│       ├── crontab            # repo-owned schedule contract
│       └── trigger-scheduled.sh
├── app/
│   ├── api/routes.py          # keep /runs/trigger/scheduled as the scheduler seam
│   ├── services/scheduling.py # ET schedule key + DB dedupe
│   └── ops/readiness.py       # app health/readiness checks
└── tests/
    ├── ops/                   # compose/scheduler contract tests
    └── api/                   # scheduled trigger route tests
```

### Pattern 1: Separate App And Scheduler Containers

**What:** Run the API in one container and the scheduler in another container on the same Compose network.

**When to use:** Always for this phase.

**Example:**
```yaml
# Source: https://docs.docker.com/reference/compose-file/services/
services:
  postgres:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U investor -d investor"]

  app:
    build: .
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.scheduler
    env_file: .env
    depends_on:
      app:
        condition: service_healthy
```

### Pattern 2: Keep Scheduling Thin And HTTP-Based

**What:** The scheduler container should only make the authenticated HTTP call and emit logs. The application keeps dedupe, ET schedule-key calculation, and workflow start behavior.

**When to use:** Always; this is already how the repo is shaped.

**Example:**
```sh
# Source: repo seam in app/api/routes.py and Supercronic container model
curl -fsS -X POST "http://app:8000/runs/trigger/scheduled" \
  -H "X-Investor-Scheduled-Trigger: ${INVESTOR_SCHEDULED_TRIGGER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"replay":false}'
```

### Pattern 3: Healthcheck-Gated Startup

**What:** Give Postgres and the app real healthchecks, and gate scheduler startup on those checks.

**When to use:** Always; Compose startup order without healthchecks is not enough.

**Example:**
```yaml
# Source: https://docs.docker.com/reference/compose-file/services/
services:
  app:
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
  scheduler:
    depends_on:
      app:
        condition: service_healthy
```

### Pattern 4: Repo-Owned Crontab File, Not Embedded Compose Labels

**What:** Keep the schedule expression in a checked-in crontab file consumed by Supercronic, with env-driven substitution only where necessary.

**When to use:** For the single-operator repo workflow in this project.

**Example:**
```cron
# Source: https://raw.githubusercontent.com/aptible/supercronic/main/README.md
CRON_TZ=America/New_York
0 7 * * 1-5 /app/ops/scheduler/trigger-scheduled.sh
```

### Anti-Patterns to Avoid

- **Docker-socket scheduler by default:** Ofelia can work, but do not make Docker socket access the baseline for a scheduler that only needs to hit one HTTP endpoint.
- **Two long-running processes in the web container:** Avoid supervisor-style web-plus-cron containers.
- **Scheduler-owned duplicate protection:** Do not add lock files, PID files, or scheduler overlap logic as the primary guard; the app and database already own the real invariant.
- **Host-mounted log files as the main observability path:** In containers, logs should be visible through `docker compose logs`; file logs can be optional, not primary.
- **Scheduler firing before readiness:** `depends_on` without `service_healthy` is not sufficient.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron daemon behavior in containers | BusyBox `crond` wrappers or custom shell loops | Supercronic | Container env, signal, logging, and timezone behavior are already solved there. |
| Container orchestration for one schedule | Custom scheduler loop in Python or bash | Docker Compose service + Supercronic | Lower complexity and keeps scheduling operationally explicit. |
| Service readiness sequencing | `sleep 10` startup hacks | Compose healthchecks + `depends_on.condition: service_healthy` | Fixed delays are brittle and race-prone. |
| Duplicate scheduled-run prevention | Scheduler overlap flags or lock files | Existing Postgres `schedule_key` uniqueness | The app already enforces the invariant at the correct boundary. |
| Migration timing | Implicit app startup side effects | Explicit `alembic upgrade head` step/container | Scheduler must not run against stale schema. |

**Key insight:** The scheduler container should be operational plumbing only. The business rule is still "at most one primary ET market-day run," and that rule already belongs to `app/services/scheduling.py` plus Postgres.

## Common Pitfalls

### Pitfall 1: Compose Startup Order Is Mistaken For Readiness

**What goes wrong:** The scheduler starts before the API or database is actually ready and records noisy failures on boot.

**Why it happens:** Plain `depends_on` only guarantees startup ordering, not health, unless `service_healthy` is used.

**How to avoid:** Add explicit healthchecks to Postgres and app; gate scheduler on `service_healthy`.

**Warning signs:** First scheduler run after `docker compose up` fails but later manual retries succeed.

### Pitfall 2: Timezone Drift Between App And Scheduler

**What goes wrong:** The scheduler fires in one timezone while `build_schedule_key()` still computes ET dates in Python.

**Why it happens:** Container timezone defaults differ, or `tzdata` is missing.

**How to avoid:** Install `tzdata`, set `TZ` in both containers, and keep `CRON_TZ=America/New_York` in the scheduler crontab.

**Warning signs:** Jobs fire at the wrong wall-clock time after DST or on non-ET hosts.

### Pitfall 3: The Scheduler Creates A Second Execution Path

**What goes wrong:** Container scheduling works, but it bypasses route auth, response handling, and existing dry-run assumptions.

**Why it happens:** The scheduler starts importing Python modules directly instead of calling the route.

**How to avoid:** Make the scheduler call the same `/runs/trigger/scheduled` endpoint with the same shared token contract.

**Warning signs:** Scheduler behavior diverges from `app.ops.dry_run` or route tests.

### Pitfall 4: Logs Stay In Files Instead Of Container Streams

**What goes wrong:** Operators cannot tell whether the scheduler is healthy without entering the container or inspecting bind-mounted files.

**Why it happens:** The host-cron file-log model is copied into containers unchanged.

**How to avoid:** Treat stdout/stderr as primary and make `docker compose logs -f scheduler app` the documented path.

**Warning signs:** README still tells the operator to inspect `logs/cron/daily-trigger.log` first.

### Pitfall 5: Missing Test Sources Hide Regressions

**What goes wrong:** Planning assumes the repo already has runnable scheduler tests because validation docs mention them, but the checked-in tree only has `.pyc` files under `tests/`.

**Why it happens:** Source test files are absent from the current workspace snapshot.

**How to avoid:** Make test restoration/recreation a Wave 0 task before relying on any existing scheduler validation contract.

**Warning signs:** `pytest` collection fails or test file paths referenced in docs do not exist.

## Code Examples

Verified patterns from official sources:

### Compose Dependency Health Gating
```yaml
# Source: https://docs.docker.com/reference/compose-file/services/
services:
  app:
    depends_on:
      postgres:
        condition: service_healthy
```

### Supercronic Container Crontab
```cron
# Source: https://raw.githubusercontent.com/aptible/supercronic/main/README.md
CRON_TZ=America/New_York
0 7 * * 1-5 /app/ops/scheduler/trigger-scheduled.sh
```

### Dockerfile Healthcheck
```dockerfile
# Source: https://docs.docker.com/reference/dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```

## State Of The Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Host `crontab` installs plus repo shell scripts | Scheduler sidecar container in Compose | Current recommendation for Phase 13 | Removes host scheduler drift and makes scheduling part of the shipped runtime. |
| Cron daemon inside the app container | Dedicated scheduler container | Current best practice for this repo | Cleaner process model, clearer logs, simpler restarts. |
| Docker-socket label scheduler for simple HTTP triggers | Plain scheduler container calling app route | Current recommendation | Avoids unnecessary Docker socket exposure. |

**Deprecated / outdated for this phase:**
- Host-managed `./scripts/cron-install.sh` / `crontab -l` as the primary operator contract.
- Startup sequencing based on fixed sleeps instead of healthchecks.

## Open Questions

1. **Should Phase 13 fully standardize Docker Compose as the primary runtime?**
   - What we know: The repo already uses Compose for Postgres, but the app itself still runs via bare `uvicorn` in README.
   - What's unclear: Whether Phase 13 should only containerize scheduling or should also containerize the web app as the default operator path.
   - Recommendation: Decide this before planning. The cleaner plan is to make Compose the primary runtime for app + postgres + scheduler together.

2. **Should existing host cron scripts be removed or repurposed?**
   - What we know: `scripts/cron-install.sh`, `cron-status.sh`, `cron-trigger.sh`, and `cron-remove.sh` are the current operator surface.
   - What's unclear: Whether backward-compatibility wrappers are still desired after the Docker-native cutover.
   - Recommendation: Keep at most one transitional wrapper script set; do not maintain two real scheduler systems long-term.

3. **Should Compose remain optional after this phase?**
   - What we know: A dedicated scheduler image/service is the cleanest implementation path for Phase 13.
   - What's unclear: Whether the project still wants a first-class non-Compose runtime after the scheduler migration lands.
   - Recommendation: Treat Compose as the primary operational path even if a manual dev-only `uvicorn` path remains available.

4. **What requirement IDs should Phase 13 carry?**
   - What we know: The roadmap lists `Requirements: TBD`.
   - What's unclear: Whether this phase replaces `SCHD-01..03`, extends them, or introduces new Phase 13-specific IDs.
   - Recommendation: Mint explicit Phase 13 requirement IDs before writing PLAN.md so tests and verification can map cleanly.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest 7.1.2` |
| Config file | none detected in repo root |
| Quick run command | `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map

Requirement IDs are not defined yet in the roadmap. Use these behaviors as the temporary planning map until Phase 13 IDs are minted.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TBD-13-01 | Compose-managed scheduler triggers the existing scheduled route without host cron | ops/integration | `python -m pytest tests/ops/test_docker_scheduler.py -q` | ❌ Wave 0 |
| TBD-13-02 | Scheduled runs still dedupe to one primary ET market-day run | api/integration | `python -m pytest tests/api/test_scheduling.py tests/integration/test_scheduled_submission_flow.py -q` | ❌ source files missing in workspace |
| TBD-13-03 | Scheduler/app logs and readiness are observable through Compose-native paths | ops | `python -m pytest tests/ops/test_docker_scheduler.py tests/ops/test_operational_docs.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py -q`
- **Per wave merge:** `python -m pytest tests/ops/test_docker_scheduler.py tests/api/test_scheduling.py tests/ops/test_operational_docs.py -q`
- **Phase gate:** `python -m pytest -q` plus one live `docker compose up` smoke check that shows `scheduler` calling the route successfully

### Wave 0 Gaps

- [ ] `Dockerfile` — app container build does not exist yet
- [ ] `.dockerignore` — build context guard does not exist yet
- [ ] Scheduler asset directory such as `ops/scheduler/` — crontab and trigger wrapper do not exist yet
- [ ] `tests/ops/test_docker_scheduler.py` — new Compose/scheduler contract test file
- [ ] `tests/api/test_scheduling.py` source file — referenced by prior docs, but absent from current workspace
- [ ] `tests/ops/test_cron_scripts.py` source file — referenced by prior docs, but absent from current workspace

## Sources

### Primary (HIGH confidence)

- https://raw.githubusercontent.com/aptible/supercronic/main/README.md - container-specific cron behavior, env inheritance, logging, signal handling, timezone support, overlap behavior
- https://github.com/aptible/supercronic/releases - current release line for Supercronic (`v0.2.43`)
- https://docs.docker.com/reference/compose-file/services/ - `depends_on.condition: service_healthy`, `env_file`, service DNS, healthchecks
- https://docs.docker.com/reference/dockerfile - `HEALTHCHECK` behavior and semantics
- https://github.com/mcuadros/ofelia/releases - current stable Ofelia release (`v0.3.21`)
- https://raw.githubusercontent.com/mcuadros/ofelia/master/README.md - Ofelia Docker-socket and label-driven model

### Secondary (MEDIUM confidence)

- Internal repo sources:
  - `app/api/routes.py`
  - `app/services/scheduling.py`
  - `app/ops/dry_run.py`
  - `docker-compose.yml`
  - `README.md`

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - primary recommendation is directly supported by official Supercronic and Docker docs plus the repo's current runtime seam
- Architecture: HIGH - based on the existing route/dedupe design in repo code and verified Compose readiness behavior
- Pitfalls: HIGH - directly supported by official scheduler/container docs and current repo gaps

**Research date:** 2026-04-02
**Valid until:** 2026-05-02
