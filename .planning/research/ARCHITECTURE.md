# Architecture Research: Investor

**Date:** 2026-03-31

## Target Component Model

### 1. Trigger Layer

- Local cron entry invokes a repo script
- The script loads env, performs basic lock/idempotency checks, and calls the application trigger path
- Purpose: make scheduling reproducible and repo-owned

### 2. API And App Runtime

- FastAPI exposes:
  - health
  - manual trigger
  - approval callback
  - optional dry-run/admin-safe debug endpoints
- Purpose: keep operational interaction simple and scriptable

### 3. Workflow Runtime

- LangGraph orchestrates:
  - load context
  - gather research data
  - synthesize recommendations
  - deterministic ranking and pruning
  - compose and send email
  - await HITL approval
  - build broker prestage payload
  - finalize and audit
- Purpose: durable interrupt/resume and explicit state transitions

### 4. Research Layer

- Typed Quiver tools fetch structured datasets
- Broker context tools fetch account/buying-power and asset constraints
- Prompt layer synthesizes evidence into a strictly structured recommendation packet
- Purpose: broad discovery with bounded output shape

### 5. Policy Layer

- Deterministic risk rules
- Deterministic broker rules
- No-action/watchlist thresholds
- Purpose: keep final eligibility and safety decisions outside the model

### 6. Delivery And HITL Layer

- Email provider abstraction
- Approval token service
- Approval callback handling
- Purpose: turn a run into a human decision and resume the same run correctly

### 7. Persistence Layer

- Run records
- Recommendation records
- Approval events
- State transitions
- Workflow checkpoints or thread metadata
- Purpose: auditability, idempotency, and restart safety

### 8. Broker Prestage Layer

- Alpaca account and asset adapters
- Position-sizing logic
- Draft order or broker-ready order payload generation
- Purpose: create a final confirmation artifact without autonomous execution

## Data Flow

1. Cron invokes repo scheduler script
2. Script triggers a daily run with schedule metadata
3. Workflow loads account context and recent run history
4. Quiver tools collect broad signals
5. Prompted research node produces candidate set with evidence and risks
6. Deterministic filters remove invalid or low-confidence ideas
7. Workflow renders email and sends it
8. Workflow pauses durably awaiting approval
9. Approval callback verifies token and resumes the same run
10. Broker policy layer validates sizing, tradability, and buying power
11. App pre-stages Alpaca order proposals or draft orders
12. Workflow finalizes and stores artifacts

## Suggested Build Order

1. Durable workflow and persistence foundation
2. Research/data expansion and detailed prompt contracts
3. Email delivery and cron scheduling
4. Approval durability and broker prestage logic
5. Operational readiness, dry-run tooling, and final acceptance checks

## Integration Boundaries

- API should not construct complex workflow dependencies inline; use a composition layer or dependency provider
- Research prompts should depend on typed tool outputs, not raw HTTP payloads
- Broker prestage logic should sit behind a service boundary separate from the approval route
- Cron scripts should call the app, not bypass it, so all normal validation and audit logic still executes
