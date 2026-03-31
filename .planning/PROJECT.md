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
- ✓ Durable Postgres-backed run state and restart-safe approval flow validated in Phase 1
- ✓ Broad Quiver research, evidence-rich ranking, and watchlist/no-action branching validated in Phase 2
- ✓ Repo-managed cron scheduling, duplicate-safe daily execution, SMTP memo delivery, and configured public approval links validated in Phase 3

### Active

- [ ] Implement a working HITL approval path that pre-stages Alpaca broker orders for final confirmation, not direct execution
- [ ] Make the app operationally ready so the remaining setup step is filling environment variables and running the documented install/start commands
- [ ] Produce a detailed system diagram that captures the runtime flow, external services, and operator touchpoints

### Out of Scope

- Automatic live trade execution after approval — broker confirmation remains the safety boundary
- Multi-user accounts and collaborative review — v1 is a single-operator workflow
- Browser UI or admin dashboard — not required to reach an env-ready operational system
- Portfolio optimization, strategy backtesting, or autonomous model tuning — secondary to getting the daily workflow reliable

## Context

The current repository now has durable workflow state, broad Quiver research and ranking, repo-managed cron scheduling, SMTP-backed memo delivery, and signed public approval links in place. The main remaining product gaps are broker-safe approval-to-prestage behavior, final operational hardening, and a durable system diagram. The desired end state is not a demo. It is a local-first app that is ready to run once final secrets and environment variables are supplied.

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
| Use repo-managed cron instead of an internal scheduler | Simpler operations and fits the requirement for local installable scheduling | Validated in Phase 3 |
| Use email provider abstraction with SMTP implemented first | Keeps local/dev simple while preserving a path to API-based senders | Validated in Phase 3 |
| Use broad Quiver signal coverage with ranking and pruning | Research quality depends on discovery across multiple weak signals, not a single deep feed | Validated in Phase 2 |
| Send no-action or watchlist emails when evidence is weak | Avoids forcing low-confidence candidates into the HITL or broker flow | Validated in Phase 2 |
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
*Last updated: 2026-03-31 after Phase 3 completion*
