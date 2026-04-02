# Roadmap: Investor

## Overview

This roadmap turns the current investor prototype into an env-ready local app by first fixing durability and workflow correctness, then deepening research quality, then making delivery and scheduling real, then wiring approval into safe Alpaca review behavior, and finally hardening the system so the remaining step is entering environment variables and running the documented commands. The final stretch was consolidated on 2026-03-31: the previously separate execution-confirmation, trading-safety, and scheduling-proof workstreams now land together in Phase 11 because the research showed they share one operational contract and one end-to-end verification surface.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Durable Workflow Foundation** - Replace in-memory orchestration with restart-safe persisted workflow state (completed 2026-03-31)
- [x] **Phase 2: Quiver Research And Ranking** - Build the broad-signal research surface, detailed prompts, and ranking outputs (completed 2026-03-31)
- [x] **Phase 3: Scheduling And Email Delivery** - Make the daily trigger, real sender path, and approval email content operational (completed 2026-03-31)
- [x] **Phase 4: HITL And Broker Prestage** - Resume approved runs durably and create safe Alpaca draft-order artifacts (completed 2026-03-31)
- [x] **Phase 5: Operational Readiness** - Validate envs, add dry-run tooling, and close the “fill vars and run” gap (completed 2026-03-31)
- [x] **Phase 6: Replace LangGraph With A Custom Workflow Engine** - Remove graph/checkpointer semantics and own workflow persistence, approval, and transitions directly (completed 2026-03-31)
- [x] **Phase 7: Build A Loop-Based Quiver Agent** - Replace one-shot research generation with an iterative tool-using Quiver agent (completed 2026-03-31)
- [x] **Phase 8: Upgrade Outputs To Strategic Insight Reports** - Turn daily output into decision-quality insight reports with change-aware rationale (completed 2026-03-31)
- [ ] **Phase 13: Replace Host Cron Scripts With A Docker-Native Scheduler** - Move scheduling off host crontab management and into a container-native scheduler path
- [ ] **Phase 14: Deepen Watchlist Explanations And Follow-Up Guidance** - Make watchlist items explain uncertainty, missing evidence, and next investigation steps in more detail

## Phase Details

### Phase 1: Durable Workflow Foundation
**Goal**: The daily run, approval state, and audit trail survive restarts and expose correct API behavior
**Depends on**: Nothing (first phase)
**Requirements**: RUNT-01, RUNT-02, RUNT-03
**Success Criteria** (what must be TRUE):
1. Operator can trigger a run, restart the app, and still complete approval on the same run
2. Postgres contains persisted run state, approval events, recommendations, and transitions for each run
3. Expired, invalid, stale, or duplicate approval attempts return clear non-500 API responses
**Plans**: 3 plans

Plans:
- [x] 01-01: Replace the in-memory workflow store with persisted run/thread state and repository services
- [x] 01-02: Wire durable workflow invoke/resume behavior with explicit state transitions and API error mapping
- [x] 01-03: Add persistence-focused tests for restart-safe approval and audit records

### Phase 2: Quiver Research And Ranking
**Goal**: The app can gather broad Quiver signals, synthesize evidence-dense recommendations, and output ranked candidates or a no-action watchlist
**Depends on**: Phase 1
**Requirements**: RSCH-01, RSCH-02, RSCH-03, RSCH-04
**Success Criteria** (what must be TRUE):
1. Daily research uses multiple Quiver datasets instead of a single hard-coded recommendation source
2. Every recommendation shows supporting evidence, opposing evidence, risk notes, and source summary
3. Weak or conflicting evidence produces a no-action or watchlist email path instead of forced candidates
4. Deterministic ranking and pruning remove invalid or duplicate ideas before delivery
**Plans**: 3 plans

Plans:
- [x] 02-01: Expand typed Quiver tools and schemas around the required multi-signal datasets
- [x] 02-02: Implement detailed research prompt contracts and structured recommendation outputs
- [x] 02-03: Add deterministic ranking, pruning, and no-action/watchlist behavior with tests

### Phase 3: Scheduling And Email Delivery
**Goal**: The app can be scheduled locally and send real daily memos with valid approval links
**Depends on**: Phase 2
**Requirements**: SCHD-01, SCHD-02, SCHD-03, MAIL-01, MAIL-02, MAIL-03
**Success Criteria** (what must be TRUE):
1. Operator can install the cron schedule from the repo and observe the scheduled trigger path
2. Duplicate cron invocations do not create duplicate primary daily runs or duplicate email sends
3. Daily emails send through SMTP and contain correctly signed links using the configured public base URL
4. Memo content clearly communicates ranked actions, watchlist items, or no-action outcomes
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Build the scheduled trigger path, schedule-key persistence, and repo-managed cron scripts
- [x] 03-02-PLAN.md — Add SMTP provider delivery, branch-aware memo rendering, and signed public approval links
- [x] 03-03-PLAN.md — Wire duplicate-safe scheduled delivery logging and expand integration verification/docs

### Phase 4: HITL And Broker Prestage
**Goal**: Human approval resumes the persisted run and creates safe Alpaca draft-order artifacts ready for final confirmation
**Depends on**: Phase 3
**Requirements**: HITL-01, HITL-02, BRKR-01, BRKR-02, BRKR-03
**Success Criteria** (what must be TRUE):
1. Approval resumes the exact persisted run and rejection safely finalizes it without broker side effects
2. Approved recommendations create broker artifacts tied to the originating run and recommendations
3. Buying power, asset support, and order-shape checks are enforced before any broker prestage occurs
4. Paper and live broker modes are explicitly separated and validated
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Build the durable approval-state machine, explicit 4xx approval semantics, and restart-safe HITL tests
- [x] 04-02-PLAN.md — Add broker artifact persistence, Alpaca policy enforcement, and app-owned draft-order prestage services
- [x] 04-03-PLAN.md — Wire approval to broker prestage and prove approve/reject/duplicate/invalid flows with end-to-end tests

### Phase 5: Operational Readiness
**Goal**: The repo is operationally complete so adding environment variables is the remaining setup step
**Depends on**: Phase 4
**Requirements**: OPER-01, OPER-02, OPER-03
**Success Criteria** (what must be TRUE):
1. Startup fails fast with clear diagnostics when required env vars are missing or inconsistent
2. Operator can run a documented dry-run path that proves the daily workflow without hidden manual work
3. README and `.env.example` provide a clear go-live checklist for local cron, email, Quiver, and Alpaca paper mode
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md — Add startup readiness gating and a deterministic dry-run command
- [x] 05-02-PLAN.md — Lock docs and env templates to the final operator workflow

### Phase 6: Replace LangGraph With A Custom Workflow Engine
**Goal**: The app owns workflow execution, approval handling, and restart-safe step transitions without LangGraph, checkpointers, or resume semantics
**Depends on**: Phase 5
**Requirements**: SC-01, SC-02, SC-03
**Success Criteria** (what must be TRUE):
1. Runtime orchestration no longer depends on LangGraph naming, configuration, or checkpointer concepts
2. Approval and rejection execute through app-owned persisted workflow steps instead of replaying a paused state payload
3. Restart-safe trigger, approval, and broker-prestage flows remain covered by tests after the cutover
**Plans**: 4 plans

Plans:
- [x] 06-01-PLAN.md — Establish the final workflow-engine API and merge the existing Alembic branch split
- [x] 06-02-PLAN.md — Remove `thread_id`, add the Phase 6 schema migration, and implement the persisted engine core
- [x] 06-03-PLAN.md — Wire trigger and approval execution onto the persisted workflow engine with restart-safe integration coverage
- [x] 06-04-PLAN.md — Remove LangGraph dependencies, env surface, and operator docs language

### Phase 7: Build A Loop-Based Quiver Agent
**Goal**: Research runs as a bounded loop-and-tools agent that decides what Quiver evidence to inspect next instead of relying on a single prompt pass.  Look at the how-to-build-a-agent in go in ../ folder for inspiration for how to build agents. 
**Depends on**: Phase 6
**Requirements**: AGENT-01, AGENT-02, AGENT-03
**Success Criteria** (what must be TRUE):
1. The agent can make multiple Quiver tool calls in one run with explicit stop conditions and budget limits
2. Research traces show why the agent chose additional investigation steps for a ticker or thesis
3. Final recommendations still satisfy the structured candidate, watchlist, or no-action contract
**Plans**: 3 plans

Plans:
- [x] 07-01-PLAN.md — Define loop-agent contracts, prompts, and tool-capable LLM seams
- [x] 07-02-PLAN.md — Implement the bounded Quiver loop and persist trace-aware workflow state
- [x] 07-03-PLAN.md — Wire loop-agent settings, readiness checks, and dry-run operational regression coverage

### Phase 8: Upgrade Outputs To Strategic Insight Reports
**Goal**: Operator-facing output explains what changed, why it matters, and what action or follow-up research is warranted
**Depends on**: Phase 7
**Requirements**: REP-01, REP-02, REP-03
**Success Criteria** (what must be TRUE):
1. Reports explain signal changes, thesis updates, or uncertainty instead of only listing ranked tickers
2. The operator can distinguish immediate actions, defer cases, and items needing more research from the delivered report
3. Email or report output remains deterministic enough to test and review locally
**Plans**: 3 plans

Plans:
- [x] 08-01-PLAN.md — Define the strategic report contract, comparison rules, and deterministic bucket builder
- [x] 08-02-PLAN.md — Add Jinja2-backed report rendering and route email composition through templates
- [x] 08-03-PLAN.md — Wire baseline-aware strategic reports into workflow execution and persisted run state

### Phase 9: Execution Confirmation And Alpaca Order Submission
**Goal**: Superseded and merged into Phase 11 planning
**Depends on**: Phase 8
**Requirements**: Merged into SC11-02 and SC11-03
**Success Criteria** (what must be TRUE):
1. Scope moved into Phase 11 so execution confirmation and submission are planned together with the scheduled end-to-end proof
2. No separate Phase 9 execution plan is required
3. Phase 11 carries the concrete implementation and verification prompts for this work
**Plans**: 0 plans

Plans:
- [x] Superseded on 2026-03-31 — scope folded into Phase 11
### Phase 10: Trading Safety Rails And Paper/Live Verification
**Goal**: Superseded and merged into Phase 11 planning
**Depends on**: Phase 8
**Requirements**: Merged into SC11-02 and SC11-03
**Success Criteria** (what must be TRUE):
1. Scope moved into Phase 11 so trading-safety verification is planned together with execution confirmation and scheduled proof
2. No separate Phase 10 execution plan is required
3. Phase 11 carries the concrete implementation and verification prompts for this work
**Plans**: 0 plans

Plans:
- [x] Superseded on 2026-03-31 — scope folded into Phase 11
### Phase 11: Scheduling Reliability And End-To-End Execution Proof
**Goal**: Scheduling and operational wiring are reliable enough to run the full approved execution flow at the intended market-open cadence
**Depends on**: Phase 8
**Requirements**: SC11-01, SC11-02, SC11-03
**Success Criteria** (what must be TRUE):
1. Scheduling supports a real `7:00am ET` configuration path wired through repo config and cron install scripts
2. The scheduled run, memo delivery, approval links, execution confirmation, and submission path work together without hidden manual glue
3. End-to-end tests cover scheduled run to submitted order behavior
**Plans**: 3 plans

Plans:
- [x] 11-01-PLAN.md — Replace hard-coded cron timing with a repo-configured 7:00am ET install/status contract
- [x] 11-02-PLAN.md — Wire the repo-local proof path through the existing execution confirmation and submission seams
- [x] 11-03-PLAN.md — Add scheduled-to-submitted integration proof and reconcile any remaining lifecycle gaps

### Phase 12: System Diagram And README Architecture Capture
**Goal**: The repo includes a complete, highly legible system diagram that shows all major components and their relationships, plus a README screenshot for quick orientation
**Depends on**: Phase 11
**Requirements**: ARCH-01, ARCH-02, ARCH-03
**Success Criteria** (what must be TRUE):
1. An Excalidraw system diagram covers the end-to-end workflow, external services, storage, automation, and operator touchpoints
2. The layout is deliberately spaced and organized for clear inspection rather than dense or overlapping placement
3. A screenshot of the diagram is added to the README so the architecture is visible from the repo entry point
**Plans**: 2 plans

Plans:
- [x] 12-01-PLAN.md — Lock the live architecture inventory and create the repo-owned Excalidraw source asset
- [x] 12-02-PLAN.md — Export the README screenshot, wire the architecture section, and add drift guards

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Durable Workflow Foundation | 3/3 | Complete   | 2026-03-31 |
| 2. Quiver Research And Ranking | 3/3 | Complete | 2026-03-31 |
| 3. Scheduling And Email Delivery | 3/3 | Complete | 2026-03-31 |
| 4. HITL And Broker Prestage | 3/3 | Complete | 2026-03-31 |
| 5. Operational Readiness | 2/2 | Complete | 2026-03-31 |
| 6. Replace LangGraph With A Custom Workflow Engine | 4/4 | Complete | 2026-03-31 |
| 7. Build A Loop-Based Quiver Agent | 3/3 | Complete   | 2026-03-31 |
| 8. Upgrade Outputs To Strategic Insight Reports | 3/3 | Complete | 2026-03-31 |
| 9. Execution Confirmation And Alpaca Order Submission | 0/0 | Merged into Phase 11 | — |
| 10. Trading Safety Rails And Paper/Live Verification | 0/0 | Merged into Phase 11 | — |
| 11. Scheduling Reliability And End-To-End Execution Proof | 3/3 | Complete   | 2026-04-01 |
| 12. System Diagram And README Architecture Capture | 2/2 | Complete | 2026-04-01 |
| 13. Replace Host Cron Scripts With A Docker-Native Scheduler | 3/3 | Complete | 2026-04-02 |
| 14. Deepen Watchlist Explanations And Follow-Up Guidance | 2/3 | In Progress|  |

### Phase 13: Replace host cron scripts with a docker-native scheduler

**Goal:** The scheduled workflow runs from the shipped Docker Compose stack, with the app container owning the repo-managed scheduler process, while the existing scheduled route and Postgres dedupe semantics stay intact
**Requirements**: TBD-13-01, TBD-13-02, TBD-13-03
**Depends on:** Phase 12
**Plans:** 3 plans

Plans:
- [x] 13-01-PLAN.md — Restore the missing scheduling test harness and add the base app-container scheduler assets
- [x] 13-02-PLAN.md — Wire the three-service Compose runtime so the app container owns scheduling and preserve dedupe behavior
- [x] 13-03-PLAN.md — Remove the host cron operator path and lock docs to the app-managed Docker scheduler workflow

### Phase 14: Deepen watchlist explanations and follow-up guidance

**Goal:** Watchlist and no-action reports explain why ideas are not yet actionable, what evidence is missing, and what to investigate next through persisted structured report fields and rendered memo sections
**Requirements**: WLG-01, WLG-02, WLG-03
**Depends on:** Phase 13
**Plans:** 2/3 plans executed

Plans:
- [ ] 14-01-PLAN.md — Restore report tests and upgrade the watchlist/report schema contract with explicit guidance fields
- [ ] 14-02-PLAN.md — Enrich the research prompt and deterministic builder for explicit watchlist guidance
- [ ] 14-03-PLAN.md — Render, persist, and document the richer watchlist guidance with verification coverage
