# Structure

## Top-Level Layout

- `app/` — main application package
- `tests/` — pytest suite covering API, graph, services, and tool adapters
- `docs/specs/` — product spec snapshot
- `docs/superpowers/` — design and planning artifacts created by the workflow tooling
- `docker-compose.yml` — local Postgres runtime
- `pyproject.toml` — package metadata and test configuration
- `README.md` — setup and verification instructions
- `AGENTS.md` — repo-specific workflow rules
- `superpower.sh`, `gsd-all.sh` — local shell helpers

## Application Package Layout

- `app/main.py` — FastAPI app factory and app-level state initialization
- `app/config.py` — environment-backed settings
- `app/api/routes.py` — HTTP routes
- `app/agents/research.py` — research-node abstraction
- `app/graph/workflow.py` — workflow orchestration
- `app/schemas/workflow.py` — Pydantic models
- `app/services/` — deterministic domain services
- `app/tools/` — typed HTTP adapters
- `app/db/` — ORM models, sessions, and migrations

## Tests Layout

- `tests/api/test_routes.py` — route-level behavior checks
- `tests/graph/test_research_node.py` — research-node JSON parsing
- `tests/graph/test_workflow.py` — invoke/resume workflow behavior
- `tests/services/*.py` — service-level logic for tokens, risk, handoff, email, persistence
- `tests/tools/test_clients.py` — HTTP adapter behavior with `httpx.MockTransport`
- `tests/conftest.py` — shared test environment defaults
- `tests/superpower_smoke_test.sh` — shell-level smoke coverage for helper tooling

## Naming And Module Patterns

- Package names are short and domain-oriented: `api`, `agents`, `graph`, `services`, `tools`, `db`.
- Most modules expose one primary concept:
  - `tokens.py`
  - `risk.py`
  - `handoff.py`
  - `workflow.py`
- Test file names mirror application module intent closely.

## Expansion Pressure Points

- `app/api/routes.py` currently owns dependency construction and workflow-store lookup; this is a likely split point as the service grows.
- `app/schemas/workflow.py` is a catch-all schema file and may need decomposition if new workflow states and payloads are added.
- `app/db/models.py` holds all ORM models in one module, which is fine at current size but will grow crowded if persistence becomes real runtime behavior.
