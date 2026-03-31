# investor

Local-first Python service for a LangGraph-driven investing workflow.

## Setup

1. Create a virtual environment with Python 3.12.
2. Install dependencies with `pip install -e .`.
3. Copy `.env.example` to `.env`.
4. Start Postgres with `docker compose up -d postgres`.
5. Run the API with `uvicorn app.main:app --reload`.

## Verification

- Run `pytest -v`.
- Check `GET /health` returns `{"status": "ok"}`.
- Trigger a run with `POST /runs/trigger`.
- Approve via the signed `/approval/{token}` callback and confirm the returned payload includes an Alpaca handoff artifact.

## Current contents

- product design spec in `docs/specs/`
- `AGENTS.md` with repo workflow rules
- `superpower.sh` developer helper script
- FastAPI service bootstrap, workflow routes, persistence models, and test suite
