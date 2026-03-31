# Pitfalls Research: Investor

**Date:** 2026-03-31

## 1. Prototype Logic Survives Into Production

- **Risk:** In-memory workflow state, fake approval URLs, or stub email paths remain in the final system
- **Warning signs:** Tests stay green while restart behavior or actual emailed links are never exercised
- **Prevention:** Add integration tests for generated approval links, restart-safe resume, and real sender adapters
- **Phase:** 1, 3, 4

## 2. Duplicate Daily Runs

- **Risk:** Cron fires twice or a retry duplicates email and broker prestage
- **Warning signs:** Multiple runs for the same market day, repeated subjects, duplicate client order IDs
- **Prevention:** Persist schedule keys and enforce one successful run per intended time window unless explicitly replayed
- **Phase:** 1, 3

## 3. Weak Signals Become False Confidence

- **Risk:** Broad Quiver coverage creates noisy candidates without enough evidence quality
- **Warning signs:** Recommendations rely on one sensational signal or omit contradictory evidence
- **Prevention:** Require prompts to separate supporting evidence, opposing evidence, and unknowns; keep deterministic minimum thresholds
- **Phase:** 2

## 4. Authenticated API Assumptions Drift

- **Risk:** Quiver dataset names, field names, or plan-tier access differ from public examples
- **Warning signs:** Tool adapters hard-code guessed fields and break once real credentials are supplied
- **Prevention:** Implement tools against authenticated docs/account responses and keep schema fixtures from real samples
- **Phase:** 2

## 5. Approval Path Is Safe On Happy Path Only

- **Risk:** Expired tokens, stale run IDs, double-click approvals, or restarted processes create invalid state
- **Warning signs:** 500 responses from approval route or duplicate prestage attempts
- **Prevention:** Add explicit approval-state machine checks, idempotent approval handling, and clear user-facing error responses
- **Phase:** 1, 4

## 6. Broker Paper And Live Modes Get Mixed

- **Risk:** Live credentials or endpoints are used when testing prestage logic
- **Warning signs:** Unclear environment names, shared env vars, or missing startup validation
- **Prevention:** Separate paper/live config, validate mode at startup, and default to paper until explicitly overridden
- **Phase:** 4, 5

## 7. Order Payloads Ignore Asset Constraints

- **Risk:** Fractional support, asset tradability, market hours, or buying power checks are skipped
- **Warning signs:** Prestage succeeds for symbols that cannot actually be submitted safely
- **Prevention:** Add deterministic broker-policy validation before any draft order is created
- **Phase:** 4

## 8. “Ready Except Env Vars” Still Hides Manual Setup

- **Risk:** Final setup still requires undocumented cron commands, migrations, or smoke checks
- **Warning signs:** Operator has to infer install steps from code instead of README/scripts
- **Prevention:** Add repo-managed install scripts, startup checks, dry-run commands, and explicit go-live checklist
- **Phase:** 3, 5
