# investor

Local-first Python service for a LangGraph-driven investing workflow.

## Setup

1. Create a virtual environment with Python 3.12.
2. Install dependencies with `pip install -e .`.
3. Copy `.env.example` to `.env`.
4. Start Postgres with `docker compose up -d postgres`.
5. Run the API with `uvicorn app.main:app --reload`.

## Verification

- Run `pytest tests/services/test_persistence.py tests/api/test_routes.py tests/integration/test_durable_workflow.py -q`.
- Run `docker compose up -d postgres && INVESTOR_DATABASE_URL=postgresql://investor:investor@localhost:5432/investor INVESTOR_LANGGRAPH_CHECKPOINTER_URL=postgresql://investor:investor@localhost:5432/investor pytest tests/integration/test_durable_workflow.py -q`.
- Run `./scripts/cron-install.sh`.
- Run `./scripts/cron-status.sh` and confirm it reports `managed=present`.
- Run `./scripts/cron-trigger.sh` and confirm the cron log shows `scheduled_trigger result=started` or `scheduled_trigger result=duplicate`.
- Run `pytest tests/api/test_scheduling.py tests/ops/test_cron_scripts.py -q`.
- Check `GET /health` returns `{"status": "ok"}`.
- Trigger a run with `POST /runs/trigger`.
- Approve via the signed `/approval/{token}` callback and confirm the returned payload includes an Alpaca handoff artifact.
- Confirm the received SMTP message uses the configured `INVESTOR_EXTERNAL_BASE_URL` host in both approval links.
- Run `./scripts/cron-remove.sh` when you want to uninstall the managed cron block.

## Current contents

- product design spec in `docs/specs/`
- `AGENTS.md` with repo workflow rules
- `superpower.sh` developer helper script
- FastAPI service bootstrap, workflow routes, persistence models, and test suite
