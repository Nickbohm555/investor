# Investor

## What This Is

Investor is a local-first trading-research and approval app that runs a daily investing workflow, gathers broad Quiver signals, produces ranked recommendations or a no-action watchlist, emails a review memo, and after approval pre-stages broker-ready Alpaca orders for final confirmation. It is for a single operator running the service locally or on a personal server who wants a fill-in-env-vars-and-go system instead of a prototype that still needs manual glue work.

## Core Value

The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.

## Requirements

### Validated

- ✓ Local FastAPI service exposes health, trigger, and approval callback routes — existing codebase
- ✓ Deterministic recommendation filtering, signed approval-token helpers, and a structured handoff payload exist — existing codebase
- ✓ Quiver and Alpaca adapters are present with unit coverage for basic request/response mapping — existing codebase

### Active

- [ ] Replace the in-memory workflow with a durable Postgres-backed run state and restart-safe approval flow
- [ ] Add repo-managed local cron setup for scheduled daily execution and idempotent run protection
- [ ] Expand Quiver tools and prompts into a broad multi-signal research system with detailed evidence and ranking
- [ ] Deliver production-ready email composition and sending through a provider abstraction with SMTP implemented first
- [ ] Implement a working HITL approval path that pre-stages Alpaca broker orders for final confirmation, not direct execution
- [ ] Make the app operationally ready so the remaining setup step is filling environment variables and running the documented install/start commands
- [ ] Produce a detailed system diagram that captures the runtime flow, external services, and operator touchpoints

### Out of Scope

- Automatic live trade execution after approval — broker confirmation remains the safety boundary
- Multi-user accounts and collaborative review — v1 is a single-operator workflow
- Browser UI or admin dashboard — not required to reach an env-ready operational system
- Portfolio optimization, strategy backtesting, or autonomous model tuning — secondary to getting the daily workflow reliable

## Context

The current repository already contains a narrow Python/FastAPI prototype, a codebase map in `.planning/codebase/`, and a product design spec in `docs/specs/2026-03-30-investor-design.md`. The prototype proves some service boundaries, but the main gaps are durability, realistic email delivery, detailed Quiver research coverage, and a broker-safe approval-to-prestage path. The desired end state is not a demo. It is a local-first app that is ready to run once final secrets and environment variables are supplied.

The operating model is intentionally hybrid. Broad discovery and synthesis come from agentic research over Quiver and broker context, while scheduling, risk rules, persistence, approvals, and order-prestage logic remain deterministic and auditable in code. If evidence is weak or conflicting, the system should send a no-action or watchlist email rather than forcing trade candidates.

## Constraints

- **Runtime**: Keep the existing Python/FastAPI/Postgres direction — reuse the current repository shape instead of replatforming
- **Scheduling**: Cron must be managed inside the repo as local/server installable artifacts — no separate always-on scheduler service
- **Email**: Be ready for real delivery, but keep provider abstraction so SMTP works first and API-provider support can slot in cleanly
- **Broker Safety**: Approval may pre-stage Alpaca orders, but must not auto-submit live trades without final broker-side confirmation
- **Research Quality**: Quiver coverage must be broad and prompts must be detailed enough to justify recommendations with evidence, risks, and gaps
- **Deployment Readiness**: The final gap should be environment variable population, not missing workflow logic or missing operational pieces

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep the project local-first | Matches current repo, personal-operator workflow, and fastest path to usable software | — Pending |
| Use repo-managed cron instead of an internal scheduler | Simpler operations and fits the requirement for local installable scheduling | — Pending |
| Use email provider abstraction with SMTP implemented first | Keeps local/dev simple while preserving a path to API-based senders | — Pending |
| Use broad Quiver signal coverage with ranking and pruning | Research quality depends on discovery across multiple weak signals, not a single deep feed | — Pending |
| Send no-action or watchlist emails when evidence is weak | Avoids forcing low-confidence candidates into the HITL or broker flow | — Pending |
| Approval should pre-stage Alpaca orders rather than execute them | Preserves a strong human safety checkpoint before any broker action becomes final | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after initialization*
