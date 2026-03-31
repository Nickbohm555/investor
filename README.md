# investor

Local-first Python service for a LangGraph-driven investing workflow.

## Setup

1. Create a virtual environment with Python 3.12.
2. Install dependencies with `pip install -e .`.
3. Copy `.env.example` to `.env`.
4. Run the API with `uvicorn app.main:app --reload`.

## Verification

- Run `pytest tests/api/test_routes.py -v`.
- Check `GET /health` returns `{"status": "ok"}`.

## Current contents

- product design spec in `docs/specs/`
- `AGENTS.md` with repo workflow rules
- `superpower.sh` developer helper script
