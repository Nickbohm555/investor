# Conventions

## General Style

- The codebase uses straightforward Python with type hints on most public functions and methods.
- Imports are simple and mostly grouped by standard library, third-party, and local modules.
- Modules are intentionally short and focused.
- Data transfer objects use Pydantic models in `app/schemas/workflow.py`.
- Persistence models use SQLAlchemy 2 style annotations with `Mapped[...]` and `mapped_column(...)` in `app/db/models.py`.

## Naming

- Functions use descriptive snake_case names such as `filter_recommendations`, `build_alpaca_handoff`, and `verify_approval_token`.
- Classes are noun-oriented and singular:
  - `ResearchNode`
  - `QuiverClient`
  - `AlpacaClient`
  - `RunRecord`
- Test names use behavior-oriented `test_<expected_behavior>` patterns.

## Dependency Style

- External dependencies are pushed to the edges:
  - FastAPI in the API layer
  - `httpx` in tool adapters
  - SQLAlchemy in persistence
  - `itsdangerous` in token handling
- The research component receives its LLM dependency through constructor injection in `app/agents/research.py`.
- Tests use local stubs or `httpx.MockTransport` instead of network calls.

## Error Handling

- Domain-specific exceptions are defined for invalid and expired approval tokens in `app/services/tokens.py`.
- HTTP client wrappers rely on `response.raise_for_status()` and do not add local translation beyond that.
- Route handlers currently assume the happy path and do not map domain errors to explicit FastAPI error responses.

## State Management

- Runtime app state is stored directly on `app.state` in `app/main.py`.
- Workflow pause state is held in a plain dict keyed by `run_id` in `app/api/routes.py`.
- This is a simple convention rather than a formal repository or service abstraction.

## Configuration Conventions

- Environment variables use the `INVESTOR_` prefix from `app/config.py`.
- Tests override settings by setting environment variables in `tests/conftest.py`.

## Documentation Conventions

- The repository keeps planning and design artifacts under `docs/` and `.planning/`.
- Product intent is documented more thoroughly than the implementation itself; inline code comments are minimal.
