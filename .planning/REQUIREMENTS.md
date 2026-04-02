# Requirements: Investor

**Defined:** 2026-03-31
**Core Value:** The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.

## v1 Requirements

### Runtime And Persistence

- [x] **RUNT-01**: Operator can trigger a daily run that persists workflow state and survives process restart
- [x] **RUNT-02**: System stores run records, recommendation records, approval events, and state transitions in Postgres
- [x] **RUNT-03**: Operator receives explicit API responses for invalid, expired, stale, or duplicate approval attempts

### Scheduling

- [x] **SCHD-01**: Operator can install and remove the local cron schedule from repo-managed scripts
- [x] **SCHD-02**: Scheduled execution creates at most one primary run per configured market-day window unless a replay is explicitly requested
- [x] **SCHD-03**: Scheduled run loads environment variables and writes observable logs for trigger success or failure

### Research And Ranking

- [x] **RSCH-01**: System queries a broad Quiver signal set including congressional trading, insider activity, government contracts, and lobbying before ranking ideas
- [x] **RSCH-02**: Each recommendation includes supporting evidence, contradictory evidence, risk notes, and a concise source summary
- [x] **RSCH-03**: System produces ranked candidates with deterministic pruning by conviction, duplication, and broker eligibility
- [x] **RSCH-04**: System can send a no-action or watchlist memo when evidence is weak or conflicting

### Email And Approval

- [x] **MAIL-01**: System sends the daily memo through a provider abstraction with SMTP implemented for v1
- [x] **MAIL-02**: Daily memo includes ranked candidates or watchlist items, rationale, and signed approval and rejection links
- [x] **MAIL-03**: Approval links are scoped to a single run, expire correctly, and use the configured external base URL

### Human Review And Broker Logic

- [ ] **HITL-01**: Approved runs resume the same persisted workflow instance instead of creating a new one
- [ ] **HITL-02**: Rejected runs finalize safely without creating broker artifacts
- [ ] **BRKR-01**: Approved recommendations are converted into pre-staged Alpaca order proposals or draft orders for final confirmation
- [ ] **BRKR-02**: Broker prestage logic verifies buying power, tradability, supported order shape, and environment mode before creating the artifact
- [ ] **BRKR-03**: Broker artifacts are traceable to the originating run and recommendation set

### Operational Readiness

- [ ] **OPER-01**: App startup validates required environment variables and fails fast with clear diagnostics when configuration is incomplete
- [ ] **OPER-02**: Operator can run a documented dry-run path that exercises scheduling, research, email rendering, approval flow, and Alpaca paper prestage without hidden manual steps
- [ ] **OPER-03**: Repository includes an env-ready README and `.env.example` that make “fill variables and run” the final setup step

### Strategic Insight Reporting

- [ ] **REP-01**: System compares each new run against the latest prior delivered run and records explicit change summaries plus dropped tickers from that baseline
- [ ] **REP-02**: System classifies output into deterministic `immediate`, `defer`, and `research` operator buckets with rationale fields that do not depend on rendered prose
- [ ] **REP-03**: System renders deterministic operator-facing text and HTML strategic reports and persists the structured report payload for local review and testing

### Quiver Research Adaptation

- [x] **QRA-01**: The bounded research loop can use a broader documented Quiver follow-up surface and persists why each follow-up investigation was chosen
- [x] **QRA-02**: The repo includes replayable evaluation cases that score candidate, watchlist, and no-action quality without requiring live Quiver access
- [x] **QRA-03**: Prompt, budget, shortlist, or ranking changes are compared with measured evaluation deltas before becoming the new default behavior
- [x] **QRA-04**: Operator-facing research output explains evidence freshness, conflicts, and missing confirmation more clearly before approval

## v2 Requirements

### Platform Expansion

- **V2-01**: Operator has a browser dashboard for viewing run history and broker artifacts
- **V2-02**: System supports API-provider email senders beyond SMTP
- **V2-03**: System supports direct live-order submission after an additional explicit confirmation step
- **V2-04**: System supports richer portfolio and position-sizing policy models

## Out of Scope

| Feature | Reason |
|---------|--------|
| Fully autonomous trade execution | Conflicts with desired broker safety boundary |
| Multi-user accounts and permissions | Single-operator product for v1 |
| Web UI for daily operation | Not required to reach env-ready operational state |
| Backtesting suite | Adjacent product surface outside the immediate goal |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RUNT-01 | Phase 1 | Complete |
| RUNT-02 | Phase 1 | Complete |
| RUNT-03 | Phase 1 | Complete |
| SCHD-01 | Phase 3 | Complete |
| SCHD-02 | Phase 3 | Complete |
| SCHD-03 | Phase 3 | Complete |
| RSCH-01 | Phase 2 | Complete |
| RSCH-02 | Phase 2 | Complete |
| RSCH-03 | Phase 2 | Complete |
| RSCH-04 | Phase 2 | Complete |
| MAIL-01 | Phase 3 | Complete |
| MAIL-02 | Phase 3 | Complete |
| MAIL-03 | Phase 3 | Complete |
| HITL-01 | Phase 4 | Pending |
| HITL-02 | Phase 4 | Pending |
| BRKR-01 | Phase 4 | Pending |
| BRKR-02 | Phase 4 | Pending |
| BRKR-03 | Phase 4 | Pending |
| OPER-01 | Phase 5 | Pending |
| OPER-02 | Phase 5 | Pending |
| OPER-03 | Phase 5 | Pending |
| REP-01 | Phase 8 | Pending |
| REP-02 | Phase 8 | Pending |
| REP-03 | Phase 8 | Pending |
| QRA-01 | Phase 16 | Complete |
| QRA-02 | Phase 16 | Complete |
| QRA-03 | Phase 16 | Complete |
| QRA-04 | Phase 16 | Complete |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after Phase 3 completion*
