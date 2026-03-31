# Phase 5: Operational Readiness - Research

**Researched:** 2026-03-31
**Domain:** Python/FastAPI operational hardening, configuration validation, and operator dry-run workflows
**Confidence:** HIGH

## User Constraints

- No separate `CONTEXT.md` exists for this phase.
- Follow repo constraints from `AGENTS.md`: keep the change focused, do not revert unrelated work, and preserve atomic commits.
- Follow project constraints from `CLAUDE.md`: stay on the existing Python/FastAPI/Postgres direction, keep cron repo-managed, keep SMTP first behind the provider abstraction, keep Alpaca approval as prestage only, and make environment variable population the final setup step.
- Phase scope is locked by the roadmap: satisfy `OPER-01`, `OPER-02`, and `OPER-03` only.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPER-01 | App startup validates required environment variables and fails fast with clear diagnostics when configuration is incomplete | Use `pydantic-settings` required fields plus a startup readiness gate in FastAPI lifespan; aggregate config mismatches into one operator-facing error. |
| OPER-02 | Operator can run a documented dry-run path that exercises scheduling, research, email rendering, approval flow, and Alpaca paper prestage without hidden manual steps | Add one repo-owned dry-run command that boots the app in a deterministic ops mode, triggers scheduled/manual flow, captures the approval link, and completes the approval/prestage path automatically. |
| OPER-03 | Repository includes an env-ready README and `.env.example` that make “fill variables and run” the final setup step | Expand `.env.example` to all required runtime values, document go-live order, and align README commands with actual scripts, migrations, and readiness checks. |
</phase_requirements>

## Summary

Phase 5 should harden the repo around one clear operational boundary: startup must refuse to run when the environment is incomplete, inconsistent, or still using placeholder values, and the repo must provide one dry-run workflow that proves daily execution without requiring the operator to improvise steps. The current codebase is close on workflow coverage, but not on operational safety. `Settings` still contains production-looking defaults for secrets and endpoints, `create_app()` bootstraps successfully with placeholder values, `.env.example` is missing several active runtime variables, `README.md` documents a partial workflow only, and the default app composition still injects `StaticLLM` plus a static Quiver `MockTransport`.

The planning trap is to treat this as a documentation-only phase. It is not. The current startup path will happily run with `change-me` secrets, fake SMTP defaults, and no Quiver or Alpaca readiness proof. The dry-run requirement also needs a repo-owned mechanism to capture and follow the generated approval link automatically, otherwise the operator still has hidden manual work in the middle of the acceptance path.

**Primary recommendation:** Build a dedicated readiness layer around `Settings` + FastAPI lifespan, add one deterministic `python -m ...` dry-run command that proves trigger-to-prestage end to end, and only then rewrite `README.md` and `.env.example` to match that exact path.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.2 (released 2026-03-23) | App bootstrap and lifespan-managed startup checks | Native app lifespan hook is the clean place to block startup before serving requests. |
| pydantic-settings | 2.13.1 (released 2026-02-19) | Env parsing, required-field validation, CLI-friendly settings models | Already in the repo; official support covers `.env`, validation, and CLI parsing without adding another dependency. |
| SQLAlchemy | 2.0.48 (released 2026-03-02) | Runtime DB engine/session wiring | Existing persistence seam; readiness checks should validate against the same configured DB URL. |
| Alembic | 1.18.4 (released 2026-02-10) | Schema migration entry point | Production readiness should use migrations, not rely on `Base.metadata.create_all(...)` as the only bootstrap path. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HTTPX | 0.28.1 (released 2024-12-06) | Deterministic dry-run transports and external adapter doubles | Use `MockTransport` to keep the dry-run network-free where appropriate and to capture stable acceptance behavior. |
| Uvicorn | 0.42.0 (released 2026-03-16) | Local ASGI serve path | Keep the documented local run command on the existing `uvicorn app.main:app` shape. |
| pytest | 9.0.2 (released 2025-12-06) | Readiness and dry-run verification | Existing test framework; extend it instead of adding new tooling. |
| langgraph-checkpoint-postgres | 3.0.5 (released 2026-03-18) | Persisted workflow checkpoint backing | Keep using the existing checkpointer seam; readiness should verify URL shape and startup setup, not replace the runtime. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pydantic-settings` CLI/readiness model | `typer` | `typer` is fine for a larger operator CLI, but this phase only needs a narrow command surface and already has `pydantic-settings` in the stack. |
| FastAPI lifespan readiness gate | `@app.on_event("startup")` | Official FastAPI guidance now recommends lifespan; mixing both creates ambiguity. |
| HTTPX transport doubles | ad hoc monkeypatching | `MockTransport` keeps the adapter seams explicit and scales better across dry-run and tests. |

**Installation:**

```bash
pip install -e .
```

**Version verification:** Verify current package versions against PyPI before implementation planning.

```bash
python - <<'PY'
import json, urllib.request
for name in ["fastapi", "pydantic-settings", "sqlalchemy", "alembic", "httpx", "uvicorn", "pytest", "langgraph-checkpoint-postgres"]:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json") as r:
        data = json.load(r)
    print(name, data["info"]["version"])
PY
```

## Architecture Patterns

### Recommended Project Structure

```text
app/
├── config.py              # Settings model plus semantic validation helpers
├── main.py                # FastAPI lifespan, app composition, startup readiness gate
├── ops/
│   ├── readiness.py       # Config validation and external/system checks
│   └── dry_run.py         # Operator dry-run entrypoint
└── services/
    └── ...                # Reuse existing workflow/mail/broker services
scripts/
├── cron-install.sh
├── cron-remove.sh
├── cron-status.sh
└── cron-trigger.sh
tests/
├── ops/
│   ├── test_readiness.py
│   ├── test_dry_run.py
│   └── test_operational_docs.py
└── integration/
    └── test_operational_readiness.py  # optional if the dry-run is split into a higher-level smoke file
```

### Pattern 1: Split syntactic env parsing from semantic readiness checks
**What:** Let `Settings()` handle type coercion and missing required fields, then run a second explicit readiness pass for placeholder secrets, URL/mode mismatches, and missing local dependencies.
**When to use:** Always at app startup and inside the dry-run command.
**Example:**

```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_secret: str
    database_url: str
    scheduled_trigger_token: str
    quiver_api_key: str
    alpaca_api_key: str

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVESTOR_", extra="ignore")


def load_settings_or_raise() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise RuntimeError(f"Configuration invalid:\n{exc}") from exc
```

### Pattern 2: Run readiness in FastAPI lifespan, not import-time side effects
**What:** Build settings and operational dependencies inside a FastAPI lifespan context so startup failures are explicit and testable.
**When to use:** App boot, health/readiness checks, and any external resource preflight.
**Example:**

```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings_or_raise()
    report = run_readiness_checks(settings)
    if report.errors:
        raise RuntimeError(report.render())
    app.state.settings = settings
    app.state.readiness_report = report
    yield


app = FastAPI(lifespan=lifespan)
```

### Pattern 3: Dry-run as one operator command with deterministic capture points
**What:** Provide a single command that starts from repo configuration, triggers the schedule path, captures the generated approval URL, follows approval automatically, and verifies broker prestage.
**When to use:** Pre-go-live verification and regression smoke checks.
**Example:**

```python
# Source: repo pattern + https://www.python-httpx.org/advanced/transports/
import httpx


def build_quiver_transport_for_dry_run() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])
    return httpx.MockTransport(handler)
```

### Pattern 4: Schema bootstrap via Alembic, not `create_all()` alone
**What:** Keep `Base.metadata.create_all(...)` for tests if useful, but document and verify `alembic upgrade head` in the operator path.
**When to use:** Any local go-live or fresh environment bootstrap.
**Example:**

```bash
# Source: https://alembic.sqlalchemy.org/en/latest/tutorial.html
alembic upgrade head
```

### Anti-Patterns to Avoid

- **Placeholder-safe startup:** `app_secret="change-me"` and similar defaults make `OPER-01` impossible to trust.
- **Import-time bootstrapping:** failing during module import is harder to diagnose and harder to test than failing in lifespan startup.
- **Health-only readiness:** `GET /health` returning `{"status":"ok"}` without config or dependency checks is not operational proof.
- **Manual inbox-driven dry-run:** requiring the operator to open an email, copy a link, and continue manually violates the "without hidden manual work" requirement.
- **Docs that lead code:** README commands must match actual scripts and code paths, not aspirational setup.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Env parsing and missing-field detection | Custom `os.getenv()` matrix with bespoke error strings | `pydantic-settings` model construction + `ValidationError` rendering | Handles type parsing, `.env` loading, and missing fields consistently. |
| Startup/shutdown hooks | Custom import-time init or mixed startup-event patterns | FastAPI lifespan | Official pattern; easier to test and reason about. |
| HTTP integration doubles | Monkeypatching client methods everywhere | `httpx.MockTransport` | Keeps dry-run and tests aligned with adapter boundaries. |
| Schema bootstrapping | Only `Base.metadata.create_all(...)` in app startup | Alembic migrations | Avoids schema drift and makes local go-live reproducible. |
| Operator CLI for this phase | New command framework from scratch | Narrow module entrypoint or `pydantic-settings` CLI | This phase needs only a small, deterministic command surface. |

**Key insight:** The hidden complexity here is not workflow logic. It is turning existing seams into an operator-proof system boundary. Reuse the libraries already responsible for settings, app lifecycle, HTTP transports, and schema state instead of layering custom glue around them.

## Common Pitfalls

### Pitfall 1: Treating defaults as examples instead of active runtime values
**What goes wrong:** Startup succeeds with fake secrets, fake SMTP hosts, and fake trigger tokens.
**Why it happens:** `Settings` currently defines permissive defaults for almost every operational field.
**How to avoid:** Make critical fields required or explicitly reject placeholders like `change-me`, `smtp.example.com`, and `https://example.test` during readiness validation.
**Warning signs:** `python -c "from app.main import create_app; create_app()"` succeeds with no `.env`.

### Pitfall 2: Confusing app health with operational readiness
**What goes wrong:** `/health` reports OK while cron, database migrations, or integration credentials are unusable.
**Why it happens:** The current route only returns a static payload and there is no readiness report.
**How to avoid:** Keep `/health` simple if desired, but add a separate readiness function/command that validates config, schema, and local shell prerequisites.
**Warning signs:** Operators can hit `/health` but still fail the first scheduled run.

### Pitfall 3: Dry-run that still hides manual work
**What goes wrong:** The "verification" path depends on opening an email inbox, copying a signed link, or mentally stitching together commands.
**Why it happens:** The current flow exposes the approval link only inside generated email content.
**How to avoid:** In dry-run mode, capture the generated mail payload locally and advance approval automatically from the captured token.
**Warning signs:** Documentation includes "open the email and click approve" as part of the smoke test.

### Pitfall 4: Leaving the dry-run on production-shaped dependencies only
**What goes wrong:** The operator cannot prove the path without real Quiver/SMTP credentials, or the command becomes flaky and expensive.
**Why it happens:** The current runtime has external seams but no explicit ops-mode harness.
**How to avoid:** Define one deterministic dry-run profile with transport/provider doubles where needed, then separately document the real go-live checklist.
**Warning signs:** Dry-run requires live internet calls just to verify local automation.

### Pitfall 5: Letting `create_all()` mask migration drift
**What goes wrong:** Fresh local databases work in tests, but real Postgres setup diverges from the intended schema lifecycle.
**Why it happens:** `create_app()` currently calls `Base.metadata.create_all(...)` unconditionally.
**How to avoid:** Keep migration commands in the documented operator flow and add a readiness check that warns when Alembic has not been applied.
**Warning signs:** README setup never mentions `alembic upgrade head`.

### Pitfall 6: Planning around the current static research doubles as if they were real integrations
**What goes wrong:** Phase 5 appears complete while Quiver credentials and live research wiring still are not part of runtime truth.
**Why it happens:** `create_app()` still defaults to `StaticLLM()` and `_static_quiver_transport()`.
**How to avoid:** Decide explicitly whether Phase 5 keeps a deterministic dry-run harness only, or also replaces default app composition with real runtime adapters.
**Warning signs:** `.env.example` adds Quiver keys but the default app path never uses them.

## Code Examples

Verified patterns from official sources and repo-aligned usage:

### Fail fast on missing settings

```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    quiver_api_key: str
    smtp_password: str
    scheduled_trigger_token: str
```

### Lifespan-managed startup gate

```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = load_settings_or_raise()
    yield


app = FastAPI(lifespan=lifespan)
```

### Deterministic external doubles with HTTPX

```python
# Source: https://www.python-httpx.org/advanced/transports/
import httpx


def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"ok": True})


transport = httpx.MockTransport(handler)
client = httpx.Client(transport=transport)
```

### Schema upgrade in the operator path

```bash
# Source: https://alembic.sqlalchemy.org/en/latest/tutorial.html
alembic upgrade head
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` startup hooks | FastAPI lifespan context | Current FastAPI docs | Use lifespan for readiness so startup behavior is explicit and non-deprecated. |
| Ad hoc CLI parser for env-driven ops tasks | `pydantic-settings` CLI support | Current `pydantic-settings` docs | A small operator command surface can stay inside the existing settings stack. |
| Monkeypatch-heavy HTTP stubs | `httpx.MockTransport` transport seam | Established current HTTPX docs | Cleaner dry-run and adapter tests without changing service code. |
| Schema creation from ORM metadata only | Alembic migration environment | Current Alembic docs | Reproducible local bootstrap and less schema drift risk. |

**Deprecated/outdated:**

- `startup`/`shutdown` event handlers as the main new startup pattern: FastAPI now recommends lifespan instead.
- Relying on placeholder defaults for secrets and endpoints: operationally unsafe even if technically valid.

## Open Questions

1. **Does Phase 5 need to replace the default `StaticLLM` and static Quiver transport?**
   - What we know: `app/main.py` still wires deterministic doubles by default.
   - What's unclear: Whether roadmap intent is "deterministic operator dry-run only" or "actual env-backed research integrations by default".
   - Recommendation: Resolve this before planning. If unchanged, call it out explicitly in the plan as a non-go-live limitation or add a task to switch default composition.

2. **Should readiness block startup on missing Postgres migrations, or only warn?**
   - What we know: Alembic exists in-repo, but README and startup do not invoke it.
   - What's unclear: Whether the operator path should enforce `alembic upgrade head` before app boot.
   - Recommendation: At minimum, make the documented flow run Alembic; prefer blocking or clearly failing the dry-run if schema is stale.

3. **How much of the dry-run should hit real external services?**
   - What we know: Requirement language asks for a dry-run path without hidden manual work and a separate go-live checklist for Quiver/email/Alpaca paper.
   - What's unclear: Whether dry-run should be fully deterministic or partially real once env vars are configured.
   - Recommendation: Make the canonical dry-run deterministic and add a second "real integrations" acceptance checklist for go-live.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.2` |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/ops/test_readiness.py tests/ops/test_dry_run.py tests/api/test_scheduling.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPER-01 | Startup rejects missing or inconsistent env and surfaces actionable diagnostics | unit/integration | `python -m pytest tests/ops/test_readiness.py -q` | ❌ Wave 0 |
| OPER-02 | Dry-run command executes scheduling, research, email capture, approval, and broker prestage without manual intervention | integration/smoke | `python -m pytest tests/ops/test_dry_run.py -q` | ❌ Wave 0 |
| OPER-03 | README and `.env.example` cover the full env-ready setup and go-live checklist | doc/assertion | `python -m pytest tests/ops/test_operational_docs.py -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ops/test_readiness.py tests/ops/test_dry_run.py -q`
- **Per wave merge:** `python -m pytest tests/api/test_routes.py tests/api/test_scheduling.py tests/ops/test_cron_scripts.py tests/integration/test_broker_prestage.py tests/ops/test_readiness.py tests/ops/test_dry_run.py -q`
- **Phase gate:** `python -m pytest -q`

### Wave 0 Gaps

- [ ] `tests/ops/test_readiness.py` - startup validation, placeholder detection, and rendered diagnostics for `OPER-01`
- [ ] `tests/ops/test_dry_run.py` - deterministic end-to-end dry-run covering trigger through approval and prestage for `OPER-02`
- [ ] `tests/ops/test_operational_docs.py` - asserts required env keys and README checklist content for `OPER-03`
- [ ] Shared dry-run fixtures for local mail capture and adapter transports if the existing `tests/conftest.py` doubles are not enough

## Sources

### Primary (HIGH confidence)

- Repo source: `app/config.py`, `app/main.py`, `app/api/routes.py`, `scripts/cron-*.sh`, `.env.example`, `README.md`, and current test suite
- Pydantic settings docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/ - `.env` loading, validation behavior, and built-in CLI support
- FastAPI lifespan docs: https://fastapi.tiangolo.com/advanced/events/ - recommended startup/shutdown pattern and deprecation of event-based alternative for new work
- HTTPX transport docs: https://www.python-httpx.org/advanced/transports/ - `MockTransport` and transport-level testing patterns
- Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html - migration environment and operator migration flow
- PyPI package metadata:
  - https://pypi.org/project/fastapi/
  - https://pypi.org/project/pydantic-settings/
  - https://pypi.org/project/sqlalchemy/
  - https://pypi.org/project/alembic/
  - https://pypi.org/project/httpx/
  - https://pypi.org/project/uvicorn/
  - https://pypi.org/project/pytest/
  - https://pypi.org/project/langgraph-checkpoint-postgres/

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, and `.planning/research/PITFALLS.md` - useful historical project framing, but repo code and official docs were used as authority

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - directly verified against repo dependencies, official docs, and PyPI registry metadata
- Architecture: HIGH - grounded in current repo structure plus official FastAPI/Pydantic/HTTPX/Alembic patterns
- Pitfalls: HIGH - mostly derived from current code behavior and requirement mismatches visible in the repo

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
