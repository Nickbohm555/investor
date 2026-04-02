# Phase 16 Research

## Objective

Deepen the Quiver research surface using documented API capabilities and add a repeatable evaluation loop for the bounded research agent.

## Primary Source Notes

- Official Quiver docs: `https://api.quiverquant.com/docs/`
- Official OpenAPI used during planning: `https://api.quiverquant.com/static/openapi.yaml`

The currently published OpenAPI explicitly documents these relevant endpoint groups:

- `/beta/bulk/congresstrading?version=V2&page_size=50`
- `/beta/live/insiders?page_size=50&limit_codes=True`
- `/beta/historical/lobbying/SEARCHALL?page_size=5`
- `/beta/live/billSummaries?page_size=10&summary_limit=5000`

Documented fields useful for richer reasoning include:

- Congress: `Filed`, `Traded`, `Trade_Size_USD`, `Party`, `Chamber`, `Company`, `Description`, `Comments`
- Insiders: `Date`, `TransactionCode`, `Shares`, `PricePerShare`, `fileDate`
- Lobbying: `Date`, `Amount`, `Issue`, `Specific_Issue`, `Registrant`
- Bill summaries: `Title`, `Summary`, `lastAction`, `lastActionDate`, `URL`

## Planning Decisions

1. Keep the existing ticker-scoped research surface intact and add the documented bill-summary endpoint as a new follow-up tool rather than forcing it into the initial ticker bundle path.
2. Improve trace quality by recording the model's stated reason for each follow-up investigation instead of only logging the executed tool name.
3. Build a repo-owned evaluation harness around saved fixture cases so future prompt, budget, and shortlist changes can be justified with measured deltas.
4. Tune shortlist selection and prompt language only after the harness exists, and preserve deterministic tests for candidate, watchlist, and no-action branches.

## Risks

- The published OpenAPI currently exposes fewer endpoint groups than Quiver's broader product surface, so Phase 16 should not assume undocumented datasets exist.
- Bill summaries are query-based rather than ticker-native, so they should be a follow-up tool, not a required input to every run.
- Agent tuning without fixed eval cases would just be intuition in code form; the evaluation harness must land before any budget or selector change is treated as an improvement.
