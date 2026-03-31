# Requirements: Investor

**Defined:** 2026-03-31
**Core Value:** The system must produce trustworthy daily recommendations on schedule and carry approved ideas into a safe broker-review path without brittle manual steps.

## v1 Requirements

### Runtime And Persistence

- [x] **RUNT-01**: Operator can trigger a daily run that persists workflow state and survives process restart
- [x] **RUNT-02**: System stores run records, recommendation records, approval events, and state transitions in Postgres
- [x] **RUNT-03**: Operator receives explicit API responses for invalid, expired, stale, or duplicate approval attempts

### Scheduling

- [ ] **SCHD-01**: Operator can install and remove the local cron schedule from repo-managed scripts
- [ ] **SCHD-02**: Scheduled execution creates at most one primary run per configured market-day window unless a replay is explicitly requested
- [ ] **SCHD-03**: Scheduled run loads environment variables and writes observable logs for trigger success or failure

### Research And Ranking

- [x] **RSCH-01**: System queries a broad Quiver signal set including congressional trading, insider activity, government contracts, and lobbying before ranking ideas
- [ ] **RSCH-02**: Each recommendation includes supporting evidence, contradictory evidence, risk notes, and a concise source summary
- [ ] **RSCH-03**: System produces ranked candidates with deterministic pruning by conviction, duplication, and broker eligibility
- [ ] **RSCH-04**: System can send a no-action or watchlist memo when evidence is weak or conflicting

### Email And Approval

- [ ] **MAIL-01**: System sends the daily memo through a provider abstraction with SMTP implemented for v1
- [ ] **MAIL-02**: Daily memo includes ranked candidates or watchlist items, rationale, and signed approval and rejection links
- [ ] **MAIL-03**: Approval links are scoped to a single run, expire correctly, and use the configured external base URL

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
| SCHD-01 | Phase 3 | Pending |
| SCHD-02 | Phase 3 | Pending |
| SCHD-03 | Phase 3 | Pending |
| RSCH-01 | Phase 2 | Complete |
| RSCH-02 | Phase 2 | Pending |
| RSCH-03 | Phase 2 | Pending |
| RSCH-04 | Phase 2 | Pending |
| MAIL-01 | Phase 3 | Pending |
| MAIL-02 | Phase 3 | Pending |
| MAIL-03 | Phase 3 | Pending |
| HITL-01 | Phase 4 | Pending |
| HITL-02 | Phase 4 | Pending |
| BRKR-01 | Phase 4 | Pending |
| BRKR-02 | Phase 4 | Pending |
| BRKR-03 | Phase 4 | Pending |
| OPER-01 | Phase 5 | Pending |
| OPER-02 | Phase 5 | Pending |
| OPER-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after initial definition*
