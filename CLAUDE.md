<!-- GSD:project-start source:PROJECT.md -->
## Project

**Investor**

Investor is a local-first trading-research and approval app that runs a daily investing workflow, gathers broad Quiver signals, produces ranked recommendations or a no-action watchlist, emails a review memo, and after approval pre-stages broker-ready Alpaca orders for final confirmation. It is for a single operator running the service locally or on a personal server who wants a fill-in-env-vars-and-go system instead of a prototype that still needs manual glue work.

**Core Value:** The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.

### Constraints

- **Runtime**: Keep the existing Python/FastAPI/Postgres direction — reuse the current repository shape instead of replatforming
- **Scheduling**: Cron must be managed inside the repo as local/server installable artifacts — no separate always-on scheduler service
- **Email**: Be ready for real delivery, but keep provider abstraction so SMTP works first and API-provider support can slot in cleanly
- **Broker Safety**: Approval may pre-stage Alpaca orders, but must not auto-submit live trades without final broker-side confirmation
- **Research Quality**: Quiver coverage must be broad and prompts must be detailed enough to justify recommendations with evidence, risks, and gaps
- **Deployment Readiness**: The final gap should be environment variable population, not missing workflow logic or missing operational pieces
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

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
## Configuration
- Environment-backed settings live in `app/config.py`.
- Supported variables from `.env.example`:
- The default `database_url` in code is SQLite (`sqlite+pysqlite:///./investor.db`) while `.env.example` points local development to Postgres (`postgresql://investor:investor@localhost:5432/investor`).
## Persistence And Infrastructure
- Docker Compose provides a local Postgres 16 instance in `docker-compose.yml`.
- SQLAlchemy models exist for:
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## General Style
- The codebase uses straightforward Python with type hints on most public functions and methods.
- Imports are simple and mostly grouped by standard library, third-party, and local modules.
- Modules are intentionally short and focused.
- Data transfer objects use Pydantic models in `app/schemas/workflow.py`.
- Persistence models use SQLAlchemy 2 style annotations with `Mapped[...]` and `mapped_column(...)` in `app/db/models.py`.
## Naming
- Functions use descriptive snake_case names such as `filter_recommendations`, `build_alpaca_handoff`, and `verify_approval_token`.
- Classes are noun-oriented and singular:
- Test names use behavior-oriented `test_<expected_behavior>` patterns.
## Dependency Style
- External dependencies are pushed to the edges:
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
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## High-Level Shape
## Layers
### API Layer
- `app/main.py`
- `app/api/routes.py`
- application setup
- route registration
- request handling
- storing shared runtime objects on `app.state`
### Workflow Orchestration Layer
- `app/graph/workflow.py`
- run research
- apply risk filtering
- compose email
- pause for approval
- resume to handoff on approval
### Agent Layer
- `app/agents/research.py`
- call an injected LLM-like object
- parse JSON output into `ResearchResult`
### Domain Schema Layer
- `app/schemas/workflow.py`
- typed recommendation schema
- typed research result schema
- typed email payload schema
### Service Layer
- `app/services/risk.py`
- `app/services/email.py`
- `app/services/tokens.py`
- `app/services/handoff.py`
- deterministic recommendation filtering
- email body generation
- token signing and verification
- structured handoff payload generation
### Data And Persistence Layer
- `app/db/models.py`
- `app/db/session.py`
- `app/db/migrations/`
- model definitions
- engine/session creation
- migrations
### External Adapter Layer
- `app/tools/quiver.py`
- `app/tools/alpaca.py`
- wrap HTTP APIs with typed methods
- isolate authentication headers and response parsing
## Data Flow
### Trigger Flow
### Approval Flow
## Architectural Strengths
- Clear file-level separation for API, services, schemas, and adapters.
- Small modules are easy to scan.
- Most domain logic is deterministic and testable in isolation.
## Architectural Gaps
- Application persistence is not part of the live runtime path.
- Workflow state is process-local and restart-sensitive.
- The `graph` package name suggests LangGraph, but the implementation is a plain Python class.
- Route handlers construct workflow dependencies directly instead of receiving them through an explicit composition layer.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
