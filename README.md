# investor

Local-first Python service for a LangGraph-driven investing workflow.

## Setup

```bash
pip install -e .
cp .env.example .env
docker compose up -d postgres
alembic upgrade head
```

Normal runtime composition now depends on the configured Quiver and OpenAI-compatible credentials rather than the old stubbed defaults.

## Dry Run

```bash
python -m app.ops.dry_run
```

Use `python -m app.ops.dry_run` as the canonical no-hidden-manual-work proof path. It runs scheduled trigger, memo generation, approval callback, and broker prestage locally by injecting deterministic doubles instead of the normal live adapters.

## Run The Service

```bash
uvicorn app.main:app --reload
```

## Cron Operations

```bash
./scripts/cron-install.sh
./scripts/cron-status.sh
./scripts/cron-trigger.sh
./scripts/cron-remove.sh
```

## Go-Live Checklist

- SMTP credentials send to the real operator inbox
- Quiver API key and base URL point to the intended account
- OpenAI-compatible API key, base URL, and model are configured for ResearchNode
- INVESTOR_EXTERNAL_BASE_URL resolves to the public approval host
- Alpaca paper mode uses https://paper-api.alpaca.markets
- Cron is installed with ./scripts/cron-install.sh and verified with ./scripts/cron-status.sh

## Acceptance Verification

```bash
python -m pytest tests/ops/test_readiness.py tests/services/test_research_llm.py tests/ops/test_dry_run.py tests/ops/test_operational_docs.py -q
python -m app.ops.dry_run
```
