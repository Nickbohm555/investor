---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed 20-03-PLAN.md
last_updated: "2026-04-04T00:48:38Z"
progress:
  total_phases: 20
  completed_phases: 16
  total_plans: 51
  completed_plans: 49
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-31)

**Core value:** The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.
**Current focus:** Phase 20 complete — direct-post-triggered-research-to-email-run-path

## Current Position

Phase: 20 (direct-post-triggered-research-to-email-run-path) — COMPLETE
Plan: 3 of 3 completed

## Performance Metrics

**Velocity:**

- Total plans completed: 12
- Average duration: 10.3 min
- Total execution time: 2.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | 16 min | 5.3 min |
| 02 | 3 | 15 min | 5.0 min |
| 03 | 3 | 64 min | 21.3 min |
| 04 | 3 | 29 min | 9.7 min |

**Recent Trend:**

- Last 5 plans: 03-02, 03-03, 04-01, 04-02, 04-03
- Trend: Stable

| Phase 03 P02 | 28 min | 2 tasks | 9 files |
| Phase 03 P03 | 23 min | 2 tasks | 9 files |
| Phase 04 P01 | 7 min | 2 tasks | 7 files |
| Phase 04 P02 | 8 min | 2 tasks | 11 files |
| Phase 04 P03 | 14 min | 2 tasks | 8 files |
| Phase 14 P02 | 4 min | 2 tasks | 4 files |

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
- [Phase 04]: Treat `broker_prestaged` as the terminal approved-state contract once broker artifacts are created. — This distinguishes a broker-ready approval path from generic workflow completion and keeps route assertions explicit.
- [Phase 04]: Persist broker draft artifacts with deterministic `client_order_id = {run_id}-{recommendation_id}-{broker_mode}` and policy snapshots. — This preserves auditability, dedupe, and future broker-confirmation seams.
- [Phase 04]: Default the shared test harness to local mail and Alpaca doubles. — This keeps restart-safe approval and broker-prestage coverage deterministic and network-free.
- [Phase 05]: Normal runtime composition uses env-backed research and Quiver configuration, while tests and the dry-run harness inject their doubles explicitly. — This removes hidden production fallbacks without losing deterministic verification seams.
- [Phase 05]: Operator docs are now locked by automated drift tests and document the dry run as the canonical local workflow proof. — This keeps README and `.env.example` aligned with the implemented runtime surface.
- [Phase 08]: Select baseline comparisons only from prior completed runs that already persisted both a strategic report and finalized outcome payload. — This keeps change detection tied to structured delivered data instead of rendered email text or in-flight runs.
- [Phase 08]: Persist `strategic_report` and `baseline_run_id` directly on paused workflow state alongside `finalized_outcome`. — Review, approval, and future tooling can inspect the same structured source of truth without recomputing the report.
- [Phase 11]: Anchor the managed cron block to 7:00am ET through shared schedule expression and timezone defaults. — This keeps cron install, status, docs, and env defaults aligned on one operator-visible contract even on non-ET hosts.
- [Phase 12]: Keep architecture docs anchored to the repo-owned Excalidraw source and the `broker_prestaged` runtime boundary. — This keeps the README screenshot derived from one editable asset and avoids presenting direct order submission as current architecture.
- [Phase 13]: Rebuild scheduler coverage around the existing dry-run doubles and scheduled-trigger route, then let the app container own Supercronic while Compose exposes only `postgres`, `migrate`, and `app`. — This preserves the proven dedupe/runtime seam while moving scheduler operations into Docker-native repo assets.
- [Phase 13]: Container migrations need explicit Alembic config, psycopg URL normalization, and a widened `alembic_version.version_num` before the Docker runtime can reach app startup. — The repo's historical revision IDs and `psycopg` dependency require bootstrap logic that the old host-run migration path hid.
- [Phase 14]: Persist watchlist guidance as explicit named fields on both watchlist candidates and research-queue report items instead of deriving everything from generic uncertainty text. — Later prompt, workflow, and rendering work now consume durable structured values rather than reconstructing explanation detail from prose.
- [Phase 14]: Keep no-action output on the same research_queue contract by supplying deterministic fallback watchlist guidance values rather than creating a second report shape. — The shared contract preserves one operator-visible report surface across watchlist and no-action outcomes.
- [Phase 14]: Keep the legacy and final prompt paths on one shared system prompt so watchlist guidance requirements cannot drift between code paths. — Both prompt entry points now enforce the same schema contract, reducing silent drift between loop-agent and legacy prompt usage.
- [Phase 14]: Once prompt-supplied watchlist guidance exists, the builder should fall back to summary-derived defaults only when those structured fields are absent. — Prompt-owned guidance should win; deterministic fallbacks remain only as safety nets when the structured fields are empty.
- [Phase 14]: Keep watchlist and no-action guidance inside one shared Research Queue section with neutral labels instead of branching to separate output formats. — One shared report surface keeps the operator memo stable while still exposing richer structured detail.
- [Phase 14]: Verify the persisted workflow payload through the existing report.model_dump(mode="python") path rather than adding duplicate persistence-specific code. — The current workflow seam already persists the strategic report payload, so tests should prove that path instead of introducing redundant logic.

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 6 added: Replace LangGraph with a custom workflow engine
- Phase 7 added: Build a loop-based Quiver agent
- Phase 8 added: Upgrade outputs to strategic insight reports
- Phase 9 added: Execution confirmation and Alpaca order submission
- Phase 10 added: Trading safety rails and paper/live verification
- Phase 11 added: Scheduling reliability and end-to-end execution proof
- Phase 12 added: System diagram and README architecture capture
- Phase 13 added: Replace host cron scripts with a docker-native scheduler
- Phase 14 added: Deepen watchlist explanations and follow-up guidance
- Phase 15 added: Prove the live Quiver-to-email workflow end to end
- Phase 16 added: Deepen Quiver signal coverage and agent evaluation
- Phase 17 added: Harden live-run approval, observability, and replay operations
- Phase 18 added: Restructure research agent around Quiver bearer-auth endpoints and live API validation
- Phase 19 added: Prove real SMTP memo delivery without approval-link dependency
- Phase 20 added: Direct POST-triggered research-to-email run path

### Blockers/Concerns

- The Docker-native smoke path now reaches app startup, but the final host bind on `8000` could not be proven on this machine because the unrelated `web-agent-backend-1` container already owns `0.0.0.0:8000`.
- A true end-to-end live proof still needs non-Quiver credentials and infrastructure that are not present in `keys.txt`: SMTP delivery settings, an OpenAI-compatible model key/base URL, and a reachable `INVESTOR_EXTERNAL_BASE_URL` for approval callbacks.
- Phase 15 live proof blocked: no live INVESTOR_* credentials loaded and host port 8000 is allocated by web-agent-backend-1, preventing app startup and external callback proof.
- Phase 19 live SMTP proof blocked: `python -m app.ops.live_proof preflight` fails with `httpx.ConnectError: [Errno 8] nodename nor servname provided, or not known` before SMTP inspection, and `docker compose up -d --build` cannot reach the Docker daemon at `unix:///Users/nickbohm/.docker/run/docker.sock`.

## Session Continuity

Last session: 2026-04-02T06:18:35.150Z
Stopped at: Completed 14-03-PLAN.md
Resume file: None
