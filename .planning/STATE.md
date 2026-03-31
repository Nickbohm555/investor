---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed 03-02-PLAN.md
last_updated: "2026-03-31T14:40:00Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 12
  completed_plans: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-31)

**Core value:** The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.
**Current focus:** Phase 03 — scheduling-and-email-delivery

## Current Position

Phase: 03 (scheduling-and-email-delivery) — EXECUTING
Plan: 2 of 3

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: Stable

| Phase 01 P01 | 5min | 2 tasks | 7 files |
| Phase 01 P02 | 7min | 2 tasks | 10 files |
| Phase 01 P03 | 4min | 2 tasks | 4 files |
| Phase 02 P02 | 4min | 2 tasks | 6 files |
| Phase 02 P03 | 7min | 2 tasks | 16 files |

## Accumulated Context

### Decisions

- Initialization: keep the app local-first and repo-scheduled with cron
- Initialization: use SMTP first behind a provider abstraction
- Initialization: use broad Quiver signal coverage with no-action/watchlist support
- Initialization: approval leads to Alpaca prestage, not auto-execution
- [Phase 01]: Separate application-owned runtime records from future LangGraph checkpoint persistence so run audit data stays straightforward to query and validate. — Needed durable app-owned records for later invoke/resume logic without coupling business queries to checkpoint storage.
- [Phase 01]: Cache only the default configured engine. Explicit database URLs used in tests create fresh engines so isolated runs do not share in-memory SQLite state. — Prevents false cross-test coupling while preserving reusable default engine behavior for app runtime code.
- [Phase 01]: Route handlers persist and validate approval state before calling the runtime resume path, so duplicate and stale callbacks are rejected from database truth instead of transient app memory. — Needed stable approval semantics across restarts and duplicate callback attempts.
- [Phase 01]: Runtime bootstrap falls back to a no-op checkpointer on non-Postgres URLs so SQLite tests can verify invoke/resume behavior without pretending to be a live checkpoint backend. — Keeps local tests honest while preserving the PostgresSaver seam for production-backed runtimes.
- [Phase 01]: Integration coverage recreates the app against the same database URL instead of simulating restart state in-memory, so restart safety is tested at the API boundary. — A real second app instance is the shortest path to proving persisted invoke/resume behavior.
- [Phase 01]: Postgres URLs are normalized to the psycopg driver in the session layer so the documented smoke command can use the repo required URL shape. — Keeps verification commands aligned with the repo documentation and declared dependency.
- [Phase 02]: Normalize all Quiver rows into uppercase per-ticker bundles before synthesis. — This keeps duplicate collapse deterministic across congress, insider, contract, and lobbying datasets.
- [Phase 02]: Treat government contracts and lobbying as contextual signals by default. — They contribute evidence and summaries, but should not behave like unconditional buy signals before ranking.
- [Phase 02]: Represent research output as explicit candidate, watchlist, and no-action branches. — Downstream workflow, ranking, and email logic can branch on validated outcome types instead of free-form result shapes.
- [Phase 02]: Inject prompt building into ResearchNode. — Tests and workflow integration can assert payload wiring while keeping the node responsible only for prompt invocation and output validation.
- [Phase 02]: Keep ranking, broker-eligibility pruning, and downgrade rules in Python after research validation. — This preserves deterministic output order and branch selection even when the research model varies.
- [Phase 02]: Persist paused workflow state payloads on the run record. — The trigger path and later resume flows need access to evidence bundles and finalized outcomes beyond the in-memory invoke response.
- [Phase 03]: Keep scheduled-run dedupe in the application/database path and keep cron responsible only for invoking the route and logging outcomes. — This preserves duplicate safety across cron, retries, and future trigger paths without relying on shell locking.
- [Phase 03]: Use the shared StaticPool SQLite harness to prove scheduled duplicate handling against the same unique-constraint seam used by app code. — This keeps duplicate-branch coverage deterministic without pretending to be PostgreSQL-only logic.
- [Phase 03]: Compose approval and rejection links inside the workflow from `external_base_url` and token settings instead of passing request-derived URLs through runtime state. — This keeps memo links stable across manual, scheduled, and future non-request trigger paths.
- [Phase 03]: Keep memo rendering structured and transport-agnostic, with provider delivery handled separately by `app.state.mail_provider`. — This preserves a clean seam for SMTP now and API-backed mail providers later.

### Pending Todos

None yet.

### Blockers/Concerns

- The documented Postgres smoke command could not be proven on this machine because the existing `localhost:5432` service rejected the documented `investor/investor` credentials.
- Phase 4 broker-prestage behavior remains out of scope for the completed durability foundation.

## Session Continuity

Last session: 2026-03-31T06:07:05.628Z
Stopped at: Completed 03-02-PLAN.md
Resume file: None
