# Roadmap: Investor

## Overview

This roadmap turns the current investor prototype into an env-ready local app by first fixing durability and workflow correctness, then deepening research quality, then making delivery and scheduling real, then wiring approval into safe Alpaca prestage behavior, and finally hardening the system so the remaining step is entering environment variables and running the documented commands.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Durable Workflow Foundation** - Replace in-memory orchestration with restart-safe persisted workflow state (completed 2026-03-31)
- [x] **Phase 2: Quiver Research And Ranking** - Build the broad-signal research surface, detailed prompts, and ranking outputs (completed 2026-03-31)
- [ ] **Phase 3: Scheduling And Email Delivery** - Make the daily trigger, real sender path, and approval email content operational
- [ ] **Phase 4: HITL And Broker Prestage** - Resume approved runs durably and create safe Alpaca draft-order artifacts
- [ ] **Phase 5: Operational Readiness** - Validate envs, add dry-run tooling, and close the “fill vars and run” gap

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
- [ ] 03-01-PLAN.md — Build the scheduled trigger path, schedule-key persistence, and repo-managed cron scripts
- [ ] 03-02-PLAN.md — Add SMTP provider delivery, branch-aware memo rendering, and signed public approval links
- [ ] 03-03-PLAN.md — Wire duplicate-safe scheduled delivery logging and expand integration verification/docs

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
- [ ] 04-01-PLAN.md — Build the durable approval-state machine, explicit 4xx approval semantics, and restart-safe HITL tests
- [ ] 04-02-PLAN.md — Add broker artifact persistence, Alpaca policy enforcement, and app-owned draft-order prestage services
- [ ] 04-03-PLAN.md — Wire approval to broker prestage and prove approve/reject/duplicate/invalid flows with end-to-end tests

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
- [ ] 05-01: Add startup validation, readiness checks, and a dry-run/verification command set
- [ ] 05-02: Finalize docs, go-live checklist, and acceptance verification against the full workflow

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Durable Workflow Foundation | 3/3 | Complete   | 2026-03-31 |
| 2. Quiver Research And Ranking | 3/3 | Complete | 2026-03-31 |
| 3. Scheduling And Email Delivery | 0/3 | Not started | - |
| 4. HITL And Broker Prestage | 0/3 | Not started | - |
| 5. Operational Readiness | 0/2 | Not started | - |
