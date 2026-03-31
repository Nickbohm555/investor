# Stack

## Languages And Runtime

- Python 3.12 is the declared runtime in `pyproject.toml`.
- The application is packaged as a single `app` Python package via setuptools in `pyproject.toml`.
- The service runs as an ASGI app from `app.main` and is intended to be served with `uvicorn`.

## Frameworks And Libraries

- FastAPI provides the HTTP service and routing in `app/main.py` and `app/api/routes.py`.
- Pydantic and `pydantic-settings` handle request-independent schemas and environment-backed settings in `app/schemas/workflow.py` and `app/config.py`.
- SQLAlchemy is present for persistence models and session creation in `app/db/models.py` and `app/db/session.py`.
- Alembic is listed as a dependency and migration files exist under `app/db/migrations/`, but migrations are not wired into any startup or developer automation path.
- `itsdangerous` is used for signed approval tokens in `app/services/tokens.py`.
- `httpx` is used for external service adapters in `app/tools/quiver.py` and `app/tools/alpaca.py`.
- `pytest` is the only declared test framework in `pyproject.toml`.

## Service Entry Points

- `app.main:create_app` builds the FastAPI application and stores runtime objects on `app.state`.
- `app.main:app` is the importable ASGI entry point for `uvicorn`.
- `app/api/routes.py` exposes:
  - `GET /health`
  - `POST /runs/trigger`
  - `GET /approval/{token}`

## Configuration

- Environment-backed settings live in `app/config.py`.
- Supported variables from `.env.example`:
  - `INVESTOR_APP_NAME`
  - `INVESTOR_APP_ENV`
  - `INVESTOR_APP_SECRET`
  - `INVESTOR_DATABASE_URL`
- The default `database_url` in code is SQLite (`sqlite+pysqlite:///./investor.db`) while `.env.example` points local development to Postgres (`postgresql://investor:investor@localhost:5432/investor`).

## Persistence And Infrastructure

- Docker Compose provides a local Postgres 16 instance in `docker-compose.yml`.
- SQLAlchemy models exist for:
  - runs
  - recommendations
  - approval events
  - state transitions
- Session management is centralized in `app/db/session.py`.
- Tests mostly use in-memory SQLite instead of the configured Postgres path.

## Developer Tooling

- `README.md` documents local setup and a basic verification flow.
- `superpower.sh` and `gsd-all.sh` are local helper scripts in the repository root.
- There is no CI configuration in the repository snapshot.

## Notable Omissions

- LangGraph is described in specs and plans but is not installed or used in the current implementation.
- No linting, formatting, or type-checking tool is declared in `pyproject.toml`.
- No production deployment or process management files are present.
