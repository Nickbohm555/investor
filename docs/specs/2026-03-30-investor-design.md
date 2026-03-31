# Investor Design

**Date:** 2026-03-30

## Goal

Build a local-first Python service named `investor` that runs a daily LangGraph workflow, uses a ReAct research agent to analyze Quiver Quantitative data, sends a recommendation email with secure approval links, pauses for human review, and resumes into an Alpaca broker handoff flow after approval.

## Scope

This spec covers only the first product slice:

- Python service
- LangGraph workflow with durable Postgres-backed checkpointing
- ReAct research agent with typed API tools
- email delivery with secure approve/reject links
- human-in-the-loop pause and resume
- Alpaca review handoff
- local development first

Out of scope for this phase:

- automated trade placement
- browser scraping as the primary data path
- MCP servers for Quiver or Alpaca
- production deployment
- admin UI
- portfolio optimization beyond simple deterministic rules

## Product Summary

The system runs each morning, gathers account context, lets a research agent make multiple Quiver API calls, synthesizes candidate trade ideas, filters them through deterministic portfolio and risk rules, emails a memo with secure approval links, pauses for approval, and on approval resumes into an Alpaca-side review handoff.

The product is intentionally hybrid. The agent handles exploratory multi-step reasoning over API tools. The workflow owns scheduling, persistence, state transitions, approvals, and broker handoff. This keeps the reasoning flexible while keeping the operational behavior auditable and bounded.

## Why LangGraph

LangGraph is the right fit because the core requirement is not just “call tools with an LLM.” The system must:

- persist workflow state in Postgres
- pause for a human approval step
- resume the same run later
- keep an inspectable audit trail

Those are workflow requirements first. The ReAct agent is one node inside that workflow, not the whole system.

## Why Not MCP

MCP is not required for v1.

Quiver and Alpaca are ordinary HTTP APIs, and the first version only needs one internal service consuming them. Direct typed clients are simpler, cheaper, and easier to test than standing up MCP servers.

MCP may become useful later if the same tools need to be shared across multiple agents, multiple apps, or external clients. It is not part of the initial architecture.

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

## Workflow

The workflow should be modeled as an explicit state machine:

1. `load_context`
   - load settings and runtime configuration
   - load account context from Alpaca
   - initialize run metadata

2. `research`
   - invoke the ReAct agent
   - allow multiple Quiver tool calls
   - collect structured trade ideas with reasons and risks

3. `risk_filter`
   - apply deterministic rules outside the LLM
   - remove low-confidence or rule-violating ideas

4. `compose_email`
   - build the daily memo
   - generate signed approval and rejection links

5. `send_email`
   - send the memo
   - persist send result and transition state

6. `await_human_review`
   - pause the workflow through LangGraph interrupt/resume behavior
   - remain durable across restarts

7. `handoff_to_alpaca`
   - build broker review payloads for approved names
   - persist handoff status

8. `finalize`
   - mark the run complete
   - store final outputs and transition log

## Research Agent Design

The research agent should be narrow and bounded.

Responsibilities:

- decide which Quiver tools to call
- synthesize multiple API responses
- explain why a stock is a candidate
- expose uncertainty and risk
- return structured outputs

Non-responsibilities:

- scheduling
- approval handling
- state persistence policy
- direct order placement
- overriding deterministic risk rules

The agent should use typed tools instead of raw prompt-only reasoning. Early tool set:

- `get_congress_trades`
- `get_insider_trades`
- `get_government_contracts`
- `get_lobbying_or_policy_signals`
- `get_current_positions`
- `get_buying_power`

The exact Quiver surface can evolve, but the pattern should remain the same: tool-based retrieval, schema-validated synthesis, and bounded execution.

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

The product database and the LangGraph checkpointer should both use Postgres, but they should be treated as separate persistence concerns.

## Human-In-The-Loop Design

The email should include secure links rather than rely on reply parsing.

Requirements:

- approval tokens must be signed
- tokens must expire
- links must map back to a single workflow run
- approval callback must resume the paused graph thread
- every decision must be logged

Local development constraint:

- if the service runs only on the local machine, approval links will only work while the machine is on and the app is reachable
- public accessibility is not required for the initial local-dev phase, but the design should avoid assumptions that block later VPS deployment

## Alpaca Handoff

The first version should not place trades automatically.

Approved recommendations should generate a broker-side review handoff. The handoff can start as a structured payload plus a clear path into Alpaca’s dashboard. The goal is to let the user review in the broker UI, not to execute from the agent.

This keeps the highest-risk operation outside the v1 system while preserving a future path toward deeper integration.

## Deterministic Risk Rules

The LLM should never be the final authority on trade eligibility.

Examples of deterministic rules the workflow should own:

- maximum number of ideas per run
- minimum conviction threshold
- disallow unsupported assets
- avoid duplicate recommendations in a recent time window
- cap suggested position size
- require required fields before email or handoff

These rules should be code-owned and testable.

## Local Development

The first version is local-development-first.

Requirements:

- Docker Compose for Postgres
- Python app can run locally against that database
- manual trigger endpoint for development
- console or low-friction email mode for local testing
- environment variables in `.env`
- `.env.example` committed, real secrets ignored

Local development is a development environment choice, not a permanent architecture choice. The system design should stay portable to a future VPS deployment.

## Repository Layout

The project should live in the standalone repo at `/Users/nickbohm/Desktop/Tinkering/investor`.

Recommended structure:

```text
investor/
  docs/
    specs/
  app/
    agents/
    db/
    graph/
    prompts/
    schemas/
    services/
    tools/
  tests/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  .env.example
  README.md
```

This structure keeps the investor project self-contained and avoids mixing its product documentation with profile-repo content. The `Nickbohm555` repo should only reference this project from its README.

## Testing Strategy

The first implementation phase should cover:

- unit tests for token signing and verification
- unit tests for deterministic risk filtering
- unit tests for Quiver and Alpaca client adapters
- workflow tests for interrupt/resume behavior
- API tests for health, manual trigger, and approval routes

The most important behavior to lock down early is the human approval pause and resume path.

## Open Questions Deferred To Planning

- exact Quiver endpoints included in v1
- email provider choice for local and future production use
- whether to use LangChain wrappers directly or lower-level model calls inside the agent node
- exact format of the Alpaca review handoff payload
- whether scheduler setup belongs in the app process or an external trigger during v1

## Success Criteria

The first implementation phase is successful if:

- a local developer can run the service against Postgres
- a manual trigger starts a LangGraph run
- the research node can call stubbed or real tools through a ReAct agent boundary
- the workflow composes and sends a daily memo
- the workflow pauses for human review
- an approval link resumes the same workflow run
- approved recommendations are converted into an Alpaca review handoff artifact
- all of the above are covered by automated tests
