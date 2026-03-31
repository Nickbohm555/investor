# Phase 3: Scheduling And Email Delivery - Research

**Researched:** 2026-03-31
**Domain:** Local cron scheduling, SMTP delivery, signed approval links, and schedule-window idempotency in a Python/FastAPI/Postgres app
**Confidence:** MEDIUM

## Summary

Phase 3 should stay on the existing Python/FastAPI/Postgres direction and make scheduling and delivery operational by adding a repo-owned cron wrapper, an application-level schedule idempotency key, and a provider-based mail service with SMTP implemented first. The cron layer should stay thin: load `.env`, write logs, and call the app trigger path. The app must own deduplication and email-send eligibility, because shell-level locking is not portable enough for this repo's macOS-first environment and would not protect future manual or retry paths.

Use Postgres uniqueness plus `INSERT ... ON CONFLICT` through SQLAlchemy for "one primary run per schedule window" behavior, and keep email composition separate from email delivery. Generate approval and rejection links from a configured external base URL, and verify tokens with expiry through `itsdangerous` plus persisted run state. The current prototype hard-codes `localhost` approval URLs and uses a no-op sender, so the plan should explicitly replace both.

The biggest planning trap is assuming the current code is close. It is not. Today the app still has in-memory workflow state, console email, no cron scripts, and no public-base-URL setting. Phase 3 planning therefore needs to target the interfaces expected after Phase 1 and Phase 2 land: durable run persistence, persisted recommendations, and deterministic ranked/watchlist/no-action outputs.

**Primary recommendation:** Plan Phase 3 around a repo-managed cron wrapper that hits a schedule-aware API trigger, with Postgres-enforced schedule uniqueness and a stdlib `EmailMessage` + `smtplib` SMTP adapter behind a mail provider interface.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCHD-01 | Operator can install and remove the local cron schedule from repo-managed scripts | Use repo-owned `install`, `remove`, and `status` scripts that manage a named crontab block and call the app trigger path rather than workflow modules directly. |
| SCHD-02 | Scheduled execution creates at most one primary run per configured market-day window unless a replay is explicitly requested | Persist a schedule-window key in Postgres and enforce uniqueness with SQLAlchemy + PostgreSQL `ON CONFLICT`; treat replay as an explicit separate path. |
| SCHD-03 | Scheduled run loads environment variables and writes observable logs for trigger success or failure | Cron wrapper should `cd` to repo root, source `.env`, emit timestamped logs, and return a non-zero exit code on trigger failure. |
| MAIL-01 | System sends the daily memo through a provider abstraction with SMTP implemented for v1 | Use a mail provider interface with an SMTP adapter first; keep rendering separate from transport so API-based senders can slot in later. |
| MAIL-02 | Daily memo includes ranked candidates or watchlist items, rationale, and signed approval and rejection links | Render memo sections explicitly for ranked actions, watchlist, and no-action paths; generate signed links per run and decision. |
| MAIL-03 | Approval links are scoped to a single run, expire correctly, and use the configured external base URL | Add `external_base_url` and approval-token TTL settings; sign tokens with `itsdangerous`, verify `max_age`, and always compose URLs from config rather than request host assumptions. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `email.message` + `smtplib` | Python 3.12 | Build SMTP-safe messages and deliver them over TLS or STARTTLS | Zero new runtime dependency, fits the current sync workflow path, and uses the standard library APIs designed for `EmailMessage` plus SMTP delivery. |
| FastAPI | 0.135.2, published 2026-03-23 | Expose health, manual trigger, scheduled trigger, and approval callback endpoints | Already the app framework; keeping cron pointed at HTTP preserves one operational trigger path. |
| SQLAlchemy | 2.0.48, published 2026-03-02 | Persist run metadata, schedule keys, and delivery state with unique constraints/upserts | Official support for PostgreSQL `ON CONFLICT` is the cleanest idempotency mechanism already aligned with the repo. |
| Alembic | 1.18.4, published 2026-02-10 | Add schedule/email columns, unique constraints, and delivery tables safely | Schema changes for schedule uniqueness and mail state should ship as first-class migrations. |
| itsdangerous | 2.2.0, published 2024-04-16 | Sign and expire approval tokens | Already in the repo and directly supports timed signature validation. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.13.1, published 2026-02-19 | SMTP, cron, public URL, and token TTL configuration | Use for all new Phase 3 settings so cron and HTTP paths read the same env-backed config. |
| httpx | 0.28.1, published 2024-12-06 | Cron wrapper can hit the app trigger path via a tiny Python CLI if shell `curl` portability becomes awkward | Use only if you prefer a repo-local Python trigger helper over raw shell HTTP calls. |
| aiosmtplib | 5.1.0, published 2026-01-25 | Async SMTP client | Use only if the email send path becomes fully async; not required for the current sync-oriented workflow. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `smtplib` | `aiosmtplib` | Better async ergonomics, but adds a dependency the current app does not need yet. |
| App-owned schedule idempotency | shell-level locking such as `flock` | `flock` is not available on this macOS machine and would not protect manual or replay triggers anyway. |
| Cron wrapper calling HTTP trigger | cron invoking workflow modules directly | Faster to prototype, but bypasses app validation, logging, and future auth/policy seams. |

**Installation:**
```bash
pip install -e .
```

**Optional async SMTP adapter:**
```bash
pip install aiosmtplib
```

**Version verification:** Current package versions were verified against PyPI on 2026-03-31 for `fastapi`, `sqlalchemy`, `alembic`, `itsdangerous`, `pydantic-settings`, `httpx`, and `aiosmtplib`.

## Architecture Patterns

### Recommended Project Structure
```text
app/
├── api/              # manual and scheduled trigger routes plus approval callback
├── services/         # mail provider, renderer, token helpers, scheduling service
├── db/               # run/delivery models, repositories, migrations
├── schemas/          # email payloads, scheduled trigger inputs, delivery results
└── main.py           # composition root
scripts/
├── cron-install.sh   # install repo-managed cron entry
├── cron-remove.sh    # remove repo-managed cron entry
├── cron-status.sh    # show installed entry and recent log path
└── cron-trigger.sh   # load env, write logs, hit scheduled trigger path
logs/
└── cron/             # append-only cron trigger logs
```

### Pattern 1: Thin Cron Wrapper, App-Owned Logic
**What:** Cron installs a repo-managed entry that changes into the repo, loads env, writes logs, and calls the app's scheduled trigger path.
**When to use:** Always for scheduled runs in this repo.
**Example:**
```bash
# Source pattern: https://man7.org/linux/man-pages/man5/crontab.5.html
SHELL=/bin/sh
MAILTO=""
PATH=/usr/bin:/bin:/usr/sbin:/sbin

30 8 * * 1-5 cd /path/to/investor && ./scripts/cron-trigger.sh >> ./logs/cron/daily.log 2>&1
```

### Pattern 2: Schedule-Window Idempotency In Postgres
**What:** Store a schedule key such as `daily:2026-03-31` or `daily:2026-03-31:preopen` on the run record and protect it with a unique constraint for primary scheduled runs.
**When to use:** For every scheduled trigger that should produce at most one primary run.
**Example:**
```python
# Source pattern: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert
from sqlalchemy.dialects.postgresql import insert

stmt = insert(RunRecord).values(
    run_id=run_id,
    schedule_key=schedule_key,
    trigger_source="cron",
    replay_of_run_id=None,
    status="queued",
)
stmt = stmt.on_conflict_do_nothing(index_elements=[RunRecord.schedule_key])
result = session.execute(stmt)

if result.rowcount == 0:
    return ExistingPrimaryRun
```

### Pattern 3: Renderer And Transport Separation
**What:** One service renders the memo from ranked/watchlist/no-action data, another transport sends it through SMTP.
**When to use:** Always; Phase 3 needs a provider abstraction, not a combined "render-and-send" blob.
**Example:**
```python
# Source patterns: https://docs.python.org/3/library/email.message.html
# and https://docs.python.org/3/library/smtplib.html
from email.message import EmailMessage
import smtplib
import ssl

message = EmailMessage()
message["Subject"] = subject
message["From"] = smtp_from
message["To"] = recipient
message.set_content(text_body)
message.add_alternative(html_body, subtype="html")

context = ssl.create_default_context()
with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as client:
    client.starttls(context=context)
    client.login(smtp_username, smtp_password)
    client.send_message(message)
```

### Pattern 4: Signed Links Built From Config, Not Host Guessing
**What:** Tokens are signed with expiry and links are composed from `external_base_url`, not `localhost` literals or incoming request headers.
**When to use:** For both approval and rejection links.
**Example:**
```python
# Source pattern: https://itsdangerous.palletsprojects.com/en/stable/timed/
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(secret_key)
token = serializer.dumps({"run_id": run_id, "decision": decision}, salt="approval-token")
payload = serializer.loads(token, salt="approval-token", max_age=ttl_seconds)
url = f"{external_base_url.rstrip('/')}/approval/{token}"
```

### Anti-Patterns to Avoid
- **Cron scripts bypassing the app:** They skip API validation, shared logging, and any future auth or replay checks.
- **Linux-only locking or crontab flags:** This machine is macOS and does not have `flock`; `crontab -h` shows only `file`, `-e`, `-l`, and `-r`, so plan for portable install/remove behavior.
- **Hard-coded `localhost` approval links:** They break the configured public-base-URL requirement and make staging/VPS deployment harder later.
- **In-memory duplicate protection:** Duplicate cron invocations are a persistence problem, not a process-local dict problem.
- **SMTP config inside the cron line:** Keep credentials in `.env` and load them through app settings, not inline in crontab entries.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timed approval tokens | Custom HMAC or JWT mini-framework | `itsdangerous` timed serializer | The repo already uses it, and it handles signing plus expiry checks cleanly. |
| MIME formatting | Manual `Content-Type` strings and boundaries | `EmailMessage.set_content()` and `add_alternative()` | MIME edge cases are easy to get wrong; the stdlib already handles them. |
| SMTP protocol details | Raw sockets or ad hoc SMTP commands | `smtplib` or `aiosmtplib` | TLS, STARTTLS, auth, and message sending are solved problems. |
| Duplicate scheduled runs | In-memory locks or PID files | Postgres unique constraints plus `ON CONFLICT` | Only the database can serialize concurrent triggers across processes safely. |
| Cron state edits | Hand-editing user crontabs in docs | Repo-managed install/remove/status scripts | Operators need one reproducible path, not manual terminal surgery. |

**Key insight:** The hard part in this phase is not sending an email or writing one cron line. It is making schedule triggers, persisted run state, and delivery behavior agree under retries and duplicate invocations.

## Common Pitfalls

### Pitfall 1: Duplicate Cron Fires Still Create Work
**What goes wrong:** Two cron fires in the same window create two primary runs or two memo sends.
**Why it happens:** Dedupe lives in shell scripts or memory instead of a unique key in Postgres.
**How to avoid:** Persist a schedule key and let the database reject the second primary insert.
**Warning signs:** Two run rows with the same market-day key, or repeated subjects for the same day.

### Pitfall 2: "Scheduled" Means Linux-Only
**What goes wrong:** Scripts rely on Cronie flags or `flock` that are absent on macOS.
**Why it happens:** Planning assumes Linux examples are portable.
**How to avoid:** Implement install/remove/status around `crontab file`, `crontab -l`, and `crontab -r`, and keep duplicate protection in the app.
**Warning signs:** `crontab` usage differences, missing `flock`, or scripts that work only in CI/Linux notes.

### Pitfall 3: Approval Links Work Only On Localhost
**What goes wrong:** Emails contain links built from `http://localhost:8000`, or from request headers that do not match the operator's public URL.
**Why it happens:** Link composition is tied to the current request rather than configuration.
**How to avoid:** Add `external_base_url` to settings and compose all approval URLs from it.
**Warning signs:** Tests only assert token substrings, not the full external URL.

### Pitfall 4: Email Rendering And Sending Are Coupled
**What goes wrong:** The workflow returns a string blob and directly sends it, making tests brittle and future providers painful.
**Why it happens:** Prototype code keeps "compose" and "send" in one service or one workflow node.
**How to avoid:** Treat renderer output and sender transport as separate seams with separate tests.
**Warning signs:** SMTP tests have to parse ranking logic, or content changes require transport rewrites.

### Pitfall 5: No-Action And Watchlist Cases Stay Implicit
**What goes wrong:** Email content only works when there are ranked buy ideas, and weak-signal days produce confusing or empty messages.
**Why it happens:** Phase 2 outputs are assumed to always contain primary recommendations.
**How to avoid:** Model three explicit memo modes: ranked actions, watchlist, and no-action.
**Warning signs:** Conditional branches that treat empty recommendations as an error instead of a valid outcome.

### Pitfall 6: Cron Env Loading Is Assumed
**What goes wrong:** Scheduled runs fail because cron has a minimal environment and does not inherit the operator's shell session.
**Why it happens:** Scripts rely on interactive shell config instead of loading `.env` deliberately.
**How to avoid:** Wrapper script should set a stable `PATH`, `cd` to repo root, and source `.env` or use a small Python launcher that loads app settings.
**Warning signs:** Manual trigger works, cron trigger fails with missing env vars or different executable paths.

## Code Examples

Verified patterns from official sources:

### Send Multipart SMTP Email
```python
# Source: https://docs.python.org/3/library/email.message.html
# Source: https://docs.python.org/3/library/smtplib.html
from email.message import EmailMessage
import smtplib
import ssl

def send_review_email(*, smtp_host: str, smtp_port: int, username: str, password: str) -> None:
    message = EmailMessage()
    message["From"] = username
    message["To"] = "operator@example.com"
    message["Subject"] = "Investor daily memo"
    message.set_content("Plain-text fallback body")
    message.add_alternative("<p>HTML body</p>", subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as client:
        client.starttls(context=context)
        client.login(username, password)
        client.send_message(message)
```

### Enforce One Primary Run Per Schedule Window
```python
# Source: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert
from sqlalchemy.dialects.postgresql import insert

def create_primary_scheduled_run(session, run_values: dict) -> bool:
    stmt = insert(RunRecord).values(**run_values)
    stmt = stmt.on_conflict_do_nothing(index_elements=[RunRecord.schedule_key])
    return session.execute(stmt).rowcount == 1
```

### Verify Timed Approval Tokens
```python
# Source: https://itsdangerous.palletsprojects.com/en/stable/timed/
from itsdangerous import URLSafeTimedSerializer

def verify_link(token: str, secret_key: str, ttl_seconds: int) -> dict:
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.loads(token, salt="approval-token", max_age=ttl_seconds)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Console/no-op email sender in app code | Real SMTP transport behind a provider interface | Current expectation for Phase 3, verified against current Python stdlib and `aiosmtplib` docs | Planner should treat real delivery as first-class, not a final polish pass. |
| Process-local duplicate protection | Database-enforced uniqueness plus upsert | Established PostgreSQL + SQLAlchemy pattern; current docs still promote `ON CONFLICT` | Idempotency belongs in persistence, not shell locking. |
| Host-derived callback URLs | Configured external base URL | Needed once emails leave localhost | Phase 3 must add config and tests for full URLs, not token fragments only. |

**Deprecated/outdated:**
- Hard-coded `http://localhost:8000/approval/...` links: outdated for any real delivery path and incompatible with `MAIL-03`.
- `send_console_email`: outdated stub that should be replaced, not extended.

## Open Questions

1. **Does "market-day window" require holiday-aware exchange calendars in v1?**
   - What we know: Requirements say "configured market-day window," not "NYSE holiday calendar."
   - What's unclear: Whether cron should skip exchange holidays automatically or only guarantee one run per configured weekday/time window.
   - Recommendation: Plan Phase 3 for explicit schedule-window config first, and only add exchange-calendar logic if the planner decides the requirement implies holiday awareness.

2. **Should the cron wrapper call HTTP directly or a repo-local Python CLI?**
   - What we know: The architecture direction says cron should call the app, not bypass it.
   - What's unclear: Whether the operator environment should depend on `curl`, or whether a tiny Python script using the project environment is preferable.
   - Recommendation: Default to a shell wrapper that uses `curl` if available; fall back to a tiny Python HTTP trigger helper if portability becomes a concern during planning.

3. **How strong must email dedupe be relative to crash-after-send scenarios?**
   - What we know: Requirements explicitly call out duplicate cron invocations, not arbitrary SMTP/network crash recovery.
   - What's unclear: Whether the planner should add an outbox/delivery table now or defer stronger exactly-once delivery semantics.
   - Recommendation: Make primary-run dedupe mandatory in Phase 3; add a persisted delivery record if Phase 1 persistence work already provides a natural place for it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` (from `pyproject.toml`) |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/services/test_email.py tests/services/test_tokens.py tests/api/test_routes.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCHD-01 | Cron install/remove/status scripts manage one repo-owned entry | smoke | `pytest tests/ops/test_cron_scripts.py::test_install_remove_status_cycle -q` | ❌ Wave 0 |
| SCHD-02 | Duplicate scheduled triggers reuse or reject a second primary run in the same window | integration | `pytest tests/api/test_scheduling.py::test_duplicate_scheduled_trigger_does_not_create_second_primary_run -q` | ❌ Wave 0 |
| SCHD-03 | Scheduled trigger path loads env and writes logs for success/failure | integration | `pytest tests/ops/test_cron_scripts.py::test_trigger_wrapper_loads_env_and_logs -q` | ❌ Wave 0 |
| MAIL-01 | Provider abstraction sends via SMTP adapter | unit | `pytest tests/services/test_mail_provider.py::test_smtp_provider_sends_emailmessage -q` | ❌ Wave 0 |
| MAIL-02 | Memo renders ranked, watchlist, and no-action content with signed links | unit | `pytest tests/services/test_email.py::test_renderer_supports_ranked_watchlist_and_no_action_paths -q` | ❌ Expand existing |
| MAIL-03 | Approval links are run-scoped, expiring, and use configured external base URL | unit/integration | `pytest tests/services/test_tokens.py tests/api/test_routes.py -q` | ✅ Partial, expand |

### Sampling Rate
- **Per task commit:** `pytest tests/services/test_email.py tests/services/test_tokens.py tests/api/test_routes.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/ops/test_cron_scripts.py` — covers `SCHD-01` and `SCHD-03`
- [ ] `tests/api/test_scheduling.py` — covers `SCHD-02`
- [ ] `tests/services/test_mail_provider.py` — covers `MAIL-01`
- [ ] Expand `tests/services/test_email.py` — covers `MAIL-02`
- [ ] Expand `tests/services/test_tokens.py` and `tests/api/test_routes.py` — covers `MAIL-03`

## Sources

### Primary (HIGH confidence)
- Python `email.message` docs: https://docs.python.org/3/library/email.message.html - verified `set_content()` and `add_alternative()` for multipart email composition
- Python `smtplib` docs: https://docs.python.org/3/library/smtplib.html - verified SMTP transport, auth, and `send_message()` path
- SQLAlchemy PostgreSQL docs: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert - verified `on_conflict_do_nothing()` / `on_conflict_do_update()` patterns
- PostgreSQL `INSERT` docs: https://www.postgresql.org/docs/current/sql-insert.html - verified `ON CONFLICT` semantics and unique-index targeting
- ItsDangerous timed-signing docs: https://itsdangerous.palletsprojects.com/en/stable/timed/ - verified timed signing and `max_age` validation
- PyPI package metadata:
  - https://pypi.org/project/fastapi/
  - https://pypi.org/project/sqlalchemy/
  - https://pypi.org/project/alembic/
  - https://pypi.org/project/itsdangerous/
  - https://pypi.org/project/pydantic-settings/
  - https://pypi.org/project/httpx/
  - https://pypi.org/project/aiosmtplib/

### Secondary (MEDIUM confidence)
- Cronie `crontab(1)` man page: https://man7.org/linux/man-pages/man1/crontab.1.html - verified install/list/remove semantics and syntax-testing capability on Linux
- Cronie `crontab(5)` man page: https://man7.org/linux/man-pages/man5/crontab.5.html - verified cron environment behavior, `MAILTO`, `PATH`, and `CRON_TZ`
- aiosmtplib usage docs: https://aiosmtplib.readthedocs.io/en/latest/usage.html - verified async SMTP alternative and STARTTLS behavior

### Tertiary (LOW confidence)
- Local macOS verification on 2026-03-31 showed `crontab` supports only `file`, `-e`, `-l`, and `-r`, and `flock` is absent on this machine. This is reliable for the current workstation but not a web-cited cross-platform claim.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - core recommendations are based on existing repo direction plus official Python/SQLAlchemy/ItsDangerous docs and current PyPI versions
- Architecture: MEDIUM - the target flow is clear, but Phase 1 and Phase 2 are not implemented yet, so some seams depend on future persistence interfaces
- Pitfalls: HIGH - they are directly supported by the current code gaps, repo constraints, and verified cron/SMTP/idempotency behavior

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
