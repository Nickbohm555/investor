# Testing

## Test Stack

- `pytest` is the only declared test framework in `pyproject.toml`.
- FastAPI route tests use `fastapi.testclient.TestClient`.
- HTTP integrations are tested with `httpx.MockTransport`.
- Persistence tests use transient in-memory SQLite created with SQLAlchemy.

## Test Organization

- API behavior: `tests/api/test_routes.py`
- Workflow and graph behavior: `tests/graph/test_research_node.py`, `tests/graph/test_workflow.py`
- Service logic: `tests/services/`
- External clients: `tests/tools/test_clients.py`

## Covered Behaviors

- app startup and health route
- manual run trigger
- approval callback happy path
- research-node JSON parsing
- workflow pause and resume path
- recommendation filtering
- token signing and expiration
- handoff payload structure
- ORM persistence of a run record
- Quiver and Alpaca client request/response mapping

## Testing Patterns

- The suite is unit-heavy and deterministic.
- Tests prefer stubs and in-process doubles over broad integration setup.
- Environment configuration is stabilized in `tests/conftest.py`.
- Assertions are narrow and behavior-focused.

## Gaps In Coverage

- No end-to-end test exercises real persistence through `app/db/session.py`.
- No test verifies Alembic migrations against a live database.
- No test covers error handling for invalid approval tokens or missing run state.
- No test checks behavior across process restarts.
- No test executes a real external API integration.
- No test exercises the actual local Postgres setup described in `README.md`.

## Verification Commands

- Documented command: `pytest -v` from `README.md`
- Current fast feedback command: `pytest -q`

## Overall Assessment

The suite is good enough to protect the current narrow implementation, but it mostly validates isolated helpers. It does not yet prove the production-intended workflow described in the specs.
