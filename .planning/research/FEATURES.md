# Feature Research: Investor

**Date:** 2026-03-31

## Table Stakes

### Workflow Runtime

- **Durable run lifecycle**
  - A daily run can be created, paused, resumed, finalized, and audited
  - Complexity: Medium
  - Dependency: Postgres-backed workflow state
- **Restart-safe approval flow**
  - Approval links still work after process restarts as long as token and run state remain valid
  - Complexity: Medium
  - Dependency: persisted run/thread state and token verification

### Scheduling

- **Repo-managed cron installation**
  - The repo can install and remove the cron entry that triggers the daily workflow
  - Complexity: Low
  - Dependency: shell scripts and documented env loading
- **Idempotent daily execution**
  - Repeated cron triggers for the same schedule window do not duplicate outputs
  - Complexity: Medium
  - Dependency: persistent run keys and duplicate guards

### Research

- **Broad Quiver signal sweep**
  - The workflow inspects multiple alternative datasets before recommending anything
  - Complexity: High
  - Dependency: typed Quiver tools and prompt contract
- **Detailed recommendation memo**
  - Every candidate includes evidence summary, why-now logic, risk notes, and missing-data caveats
  - Complexity: High
  - Dependency: prompt quality plus deterministic output schema
- **No-action/watchlist mode**
  - The system can conclude that nothing is strong enough to act on
  - Complexity: Medium
  - Dependency: ranking thresholds and email rendering

### Email And Approval

- **Real email delivery**
  - The workflow sends a real message through SMTP now, with a provider abstraction for later senders
  - Complexity: Medium
  - Dependency: sender interface and validated env vars
- **Signed approval links**
  - Approval and rejection links are expiring, single-run scoped, and human-usable
  - Complexity: Medium
  - Dependency: token service plus correct email composition

### Broker Handoff

- **Pre-staged Alpaca order proposal**
  - Approved ideas create broker-ready payloads or draft orders for final confirmation
  - Complexity: High
  - Dependency: account context, tradability checks, quantity sizing, paper/live environment handling
- **Broker safety rules**
  - The app rejects unsupported assets, insufficient buying power, and invalid order setups before prestage
  - Complexity: High
  - Dependency: deterministic broker policy layer

### Operations

- **Env-ready startup**
  - Once secrets are supplied, the app validates configuration and starts without hidden manual steps
  - Complexity: Medium
  - Dependency: startup validation and README checklist
- **Dry-run verification**
  - The repo provides a realistic verification path before live use
  - Complexity: Medium
  - Dependency: scriptable smoke path and paper broker mode

## Differentiators

- **Evidence-dense prompt contract**
  - Recommendations explicitly distinguish supporting evidence, contradictory evidence, and unknowns
- **Broad-signal ranking instead of single-source hype**
  - Candidates are ranked after aggregating multiple weak signals
- **Operator-grade audit trail**
  - Run timeline, approval events, and prestage outcomes remain inspectable after the fact
- **Graceful no-trade days**
  - The system prefers “do nothing” over low-quality action

## Anti-Features

| Anti-Feature | Why Not Now |
|--------------|-------------|
| Automatic live trade execution | Breaks the intended safety boundary |
| Browser dashboard | Adds UI scope without improving v1 readiness |
| Multi-user review workflow | Single-operator product for now |
| Strategy lab / backtesting suite | Large adjacent product, not required for daily operation |
| Overly broad social/sentiment ingestion | Easy to bloat signal quality before core workflow is stable |

## Feature Dependencies

- Scheduling is only safe once durable run identity exists
- Email approval links depend on correct persisted run and token state
- Broker prestage depends on both successful approval handling and deterministic risk/broker checks
- No-action emails depend on ranking logic and email composition being first-class, not fallback behavior
