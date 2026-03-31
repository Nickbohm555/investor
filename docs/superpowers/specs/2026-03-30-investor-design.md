# Investor Design

**Date:** 2026-03-30

## Goal

Build a local-first Python service named `investor` that runs a daily LangGraph workflow, uses a ReAct research agent to analyze Quiver Quantitative data, sends a recommendation email with secure approval links, pauses for human review, and resumes into an Alpaca broker handoff flow after approval.

## Scope

This spec covers the first implementation slice only:

- Python service
- LangGraph workflow with durable Postgres-backed checkpointing
- ReAct research agent with typed API tools
- Email delivery with secure approval links
- Human-in-the-loop pause and resume
- Alpaca review handoff
- Local development first

Out of scope for this slice:

- Automated trade placement
- Browser scraping as the primary data path
- MCP servers for Quiver or Alpaca
- Production deployment
- Admin UI
- Portfolio optimization beyond simple deterministic rules

## Product Summary

The system runs each morning, gathers account context, lets a research agent make multiple Quiver API calls, synthesizes candidate trade ideas, filters them through deterministic portfolio and risk rules, emails a memo with secure approval links, pauses for approval, and on approval resumes into an Alpaca-side review handoff.

The product is intentionally hybrid. The agent handles exploratory multi-step reasoning over API tools. The workflow owns scheduling, persistence, state transitions, approvals, and broker handoff. This keeps the reasoning flexible while keeping the operational behavior auditable and bounded.

## Architecture Decisions

### LangGraph

LangGraph is the right fit because the core requirement is workflow durability, interruption, and resume, not just tool calling. The system must persist workflow state in Postgres, pause for human approval, resume the same run later, and keep an inspectable audit trail. The ReAct agent is one node inside that workflow rather than the entire architecture.

### Direct HTTP Integrations Instead of MCP

MCP is not required for v1. Quiver and Alpaca are ordinary HTTP APIs, and the first version only needs one internal service consuming them. Direct typed clients are simpler, cheaper, and easier to test than standing up MCP servers. MCP can be revisited later if the same tools need to be shared across multiple agents or apps.

### Local-First Delivery

The initial workflow should run locally with Docker Compose for Postgres and a Python app process on the developer machine. The design must stay portable to future VPS deployment by keeping environment configuration explicit and transport assumptions minimal.

## System Architecture

The system has five major parts:

1. `API service`
   - FastAPI app
   - health endpoint
   - manual trigger endpoint for local development
   - approval callback endpoint

2. `Workflow runtime`
   - LangGraph state machine
   - Postgres-backed checkpointer
   - daily run lifecycle
   - pause/resume behavior

3. `Research agent`
   - ReAct-style agent
   - typed Quiver and Alpaca context tools
   - structured recommendation output

4. `Application persistence`
   - run records
   - recommendation records
   - approval events
   - audit log of state transitions

5. `Integration layer`
   - Quiver client
   - Alpaca client
   - email service
   - token signing and verification

## Recommended Repository Layout

```text
investor/
  docs/
    superpowers/
      specs/
      plans/
  app/
    api/
    agents/
    db/
    graph/
    prompts/
    schemas/
    services/
    tools/
  tests/
    api/
    graph/
    services/
    tools/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  .env.example
  README.md
```

This structure keeps product documentation and implementation artifacts self-contained in this repository and makes the workflow boundaries obvious to future agents.

## Workflow

The workflow should be modeled as an explicit state machine:

1. `load_context`
   - Load settings and runtime configuration
   - Load account context from Alpaca
   - Initialize run metadata

2. `research`
   - Invoke the ReAct agent
   - Allow multiple Quiver tool calls
   - Collect structured trade ideas with reasons and risks

3. `risk_filter`
   - Apply deterministic rules outside the LLM
   - Remove low-confidence or rule-violating ideas

4. `compose_email`
   - Build the daily memo
   - Generate signed approval and rejection links

5. `send_email`
   - Send the memo
   - Persist send result and transition state

6. `await_human_review`
   - Pause the workflow through LangGraph interrupt/resume behavior
   - Remain durable across restarts

7. `handoff_to_alpaca`
   - Build broker review payloads for approved names
   - Persist handoff status

8. `finalize`
   - Mark the run complete
   - Store final outputs and transition log

## Research Agent Design

The research agent should be narrow and bounded.

Responsibilities:

- Decide which Quiver tools to call
- Synthesize multiple API responses
- Explain why a stock is a candidate
- Expose uncertainty and risk
- Return structured outputs

Non-responsibilities:

- Scheduling
- Approval handling
- State persistence policy
- Direct order placement
- Overriding deterministic risk rules

The agent should use typed tools instead of raw prompt-only reasoning. The initial tool set should include:

- `get_congress_trades`
- `get_insider_trades`
- `get_government_contracts`
- `get_lobbying_or_policy_signals`
- `get_current_positions`
- `get_buying_power`

The exact Quiver endpoint list can evolve, but the architecture should remain tool-based retrieval plus schema-validated synthesis plus bounded execution.

## Data Model

The first version should persist application records in Postgres separately from LangGraph checkpoint state.

### Run Record

- `run_id`
- `scheduled_for`
- `status`
- `thread_id`
- `email_subject`
- `email_sent_at`
- `created_at`
- `updated_at`

### Recommendation Record

- `run_id`
- `ticker`
- `action`
- `conviction_score`
- `rationale`
- `risk_notes`
- `source_summary`
- `approved`

### Approval Event

- `run_id`
- `decision`
- `token_fingerprint`
- `timestamp`

### State Transition Log

- `run_id`
- `from_status`
- `to_status`
- `reason`
- `timestamp`

## Human-In-The-Loop Design

The email should include secure links rather than rely on reply parsing.

Requirements:

- Approval tokens must be signed
- Tokens must expire
- Links must map back to a single workflow run
- Approval callback must resume the paused graph thread
- Every decision must be logged

Local development constraint:

- If the service runs only on the local machine, approval links only work while the machine is on and the app is reachable
- Public accessibility is not required for the initial local-dev phase, but the design should avoid assumptions that block later deployment

## Alpaca Handoff

The first version should not place trades automatically.

Approved recommendations should generate a broker-side review handoff artifact. The artifact can start as a structured payload plus a clear path into Alpaca’s dashboard. The goal is to let the user review in the broker UI, not to execute from the agent.

## Deterministic Risk Rules

The LLM should never be the final authority on trade eligibility.

Examples of deterministic rules the workflow should own:

- Maximum number of ideas per run
- Minimum conviction threshold
- Disallow unsupported assets
- Avoid duplicate recommendations in a recent time window
- Cap suggested position size
- Require required fields before email or handoff

These rules should be code-owned and testable.

## Local Development Requirements

- Docker Compose for Postgres
- Python app can run locally against that database
- Manual trigger endpoint for development
- Console or low-friction email mode for local testing
- Environment variables in `.env`
- `.env.example` committed, real secrets ignored

## Testing Strategy

The first implementation phase should cover:

- Unit tests for token signing and verification
- Unit tests for deterministic risk filtering
- Unit tests for Quiver and Alpaca client adapters
- Workflow tests for interrupt/resume behavior
- API tests for health, manual trigger, and approval routes

The most important behavior to lock down early is the human approval pause and resume path.

## Planning Decisions Resolved

The implementation plan should assume these concrete decisions:

- Use FastAPI for the API process
- Use SQLAlchemy with Alembic for application persistence
- Use LangGraph with Postgres-backed checkpointing for workflow durability
- Use Pydantic models for workflow state and integration payloads
- Use a console email provider in local development and a pluggable service boundary for later SMTP or API-backed delivery
- Keep scheduling out of the app for v1; use the manual trigger path first and add cron or an external trigger later
- Treat Alpaca handoff as a persisted review artifact rather than execution

## Success Criteria

The first implementation phase is successful if:

- A local developer can run the service against Postgres
- A manual trigger starts a LangGraph run
- The research node can call stubbed or real tools through a ReAct agent boundary
- The workflow composes and sends a daily memo
- The workflow pauses for human review
- An approval link resumes the same workflow run
- Approved recommendations are converted into an Alpaca review handoff artifact
- All of the above are covered by automated tests
