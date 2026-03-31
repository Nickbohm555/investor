# Architecture

## High-Level Shape

The codebase is a small layered Python service organized around a FastAPI boundary and a set of narrow service modules. The runtime path is simple:

1. `app/main.py` builds the application object.
2. `app/api/routes.py` receives HTTP requests.
3. Routes construct or resume a workflow object from `app/graph/workflow.py`.
4. The workflow invokes a research node, deterministic services, and a handoff builder.
5. State is stored in `app.state.workflow_store` rather than a durable backing store.

## Layers

### API Layer

- `app/main.py`
- `app/api/routes.py`

Responsibilities:

- application setup
- route registration
- request handling
- storing shared runtime objects on `app.state`

### Workflow Orchestration Layer

- `app/graph/workflow.py`

Responsibilities:

- run research
- apply risk filtering
- compose email
- pause for approval
- resume to handoff on approval

This layer currently acts as an orchestration service object rather than a graph runtime.

### Agent Layer

- `app/agents/research.py`

Responsibilities:

- call an injected LLM-like object
- parse JSON output into `ResearchResult`

The agent abstraction is intentionally thin. It is closer to a typed adapter than a full agent framework.

### Domain Schema Layer

- `app/schemas/workflow.py`

Responsibilities:

- typed recommendation schema
- typed research result schema
- typed email payload schema

### Service Layer

- `app/services/risk.py`
- `app/services/email.py`
- `app/services/tokens.py`
- `app/services/handoff.py`

Responsibilities:

- deterministic recommendation filtering
- email body generation
- token signing and verification
- structured handoff payload generation

### Data And Persistence Layer

- `app/db/models.py`
- `app/db/session.py`
- `app/db/migrations/`

Responsibilities:

- model definitions
- engine/session creation
- migrations

This layer is mostly disconnected from the request and workflow paths today.

### External Adapter Layer

- `app/tools/quiver.py`
- `app/tools/alpaca.py`

Responsibilities:

- wrap HTTP APIs with typed methods
- isolate authentication headers and response parsing

## Data Flow

### Trigger Flow

1. `POST /runs/trigger` generates a `run_id`.
2. The route creates a workflow with a hard-coded `StaticLLM`.
3. `CompiledInvestorWorkflow.invoke()` runs research and filtering.
4. The workflow composes an email body and returns a paused-state dict.
5. The route stores that state in `request.app.state.workflow_store`.

### Approval Flow

1. `GET /approval/{token}` verifies the token.
2. The route looks up workflow state by `payload.run_id`.
3. The workflow resumes with `decision`.
4. Approval produces a handoff payload and marks status completed.

## Architectural Strengths

- Clear file-level separation for API, services, schemas, and adapters.
- Small modules are easy to scan.
- Most domain logic is deterministic and testable in isolation.

## Architectural Gaps

- Application persistence is not part of the live runtime path.
- Workflow state is process-local and restart-sensitive.
- The `graph` package name suggests LangGraph, but the implementation is a plain Python class.
- Route handlers construct workflow dependencies directly instead of receiving them through an explicit composition layer.
