# Stack Research: Investor

**Date:** 2026-03-31
**Scope:** Brownfield investor workflow app becoming env-ready for local operation

## Recommended Runtime Stack

### Application Runtime

- **Python 3.12** for the core application runtime
- **FastAPI** for HTTP routes, health checks, approval callback handling, and internal admin/dev endpoints
- **Uvicorn** for local and server execution
- **Pydantic v2 + pydantic-settings** for settings validation, schema validation, and startup env checks

### Workflow And State

- **LangGraph** for durable interrupt/resume workflow behavior
- **Postgres 16** for application records and workflow/checkpoint durability
- **SQLAlchemy + Alembic** for application data models and migrations

Why:

- The current product requirement is human approval plus resume-after-interrupt. That is a workflow problem, not just a routing problem.
- The existing codebase already points at FastAPI, SQLAlchemy, Alembic, and Postgres, so this is an extension of current direction rather than a reset.

### Scheduling

- **Repo-managed cron** as the execution trigger for the daily run
- **Shell install/uninstall/status scripts** checked into the repo
- **Idempotency guard in application code** so duplicate cron invocations do not produce duplicate emails or duplicate broker prestage attempts

Why:

- Cron is stable, local-friendly, and matches the requirement that scheduling be configured inside the repository instead of through a long-running scheduler process.

### Email Delivery

- **Provider abstraction** in app code
- **SMTP sender implemented first**
- **API-provider adapter interface** ready for Resend/Postmark-style migration later
- **Jinja2 or explicit template builder** for structured plaintext and optional HTML email bodies

Why:

- SMTP is the fastest route to an env-ready local deployment.
- Provider abstraction prevents reworking the workflow when switching senders.

### External Integrations

- **Quiver Quantitative API** as the alternative-data source
- **Alpaca Trading API** for account context and order-prestage behavior
- **httpx** for typed adapters with transport injection for tests

### Verification And Quality

- **pytest** for unit and workflow coverage
- **End-to-end dry-run command** in repo for Quiver fetch, email rendering, approval callback, and Alpaca paper prestage
- **Structured logging** for run lifecycle, approval events, broker prestage requests, and cron execution

## Quiver Data Surface To Support

Quiver’s public API landing page advertises one API with many datasets including Senate trading, House trading, insider trading, government contracts, institutional holdings, ETF holdings, and corporate lobbying. Their public Python package examples additionally show methods for congress trading, lobbying, government contracts, and insiders, which aligns well with the product’s broad-signal requirement.

Recommended first-class Quiver tool coverage for this project:

- House trading
- Senate trading
- Insider transactions
- Government contracts
- Corporate lobbying
- Institutional holdings
- ETF holdings
- Optional secondary signals once core path works:
  - patents
  - off-exchange short volume
  - Wikipedia or social attention feeds

## Alpaca Capabilities To Design Around

Alpaca’s current docs emphasize account retrieval, buying power checks, and order placement endpoints. For this project, the app should use Alpaca for:

- account snapshot and buying power
- asset metadata and tradability checks
- order payload construction
- paper-trading-safe prestage behavior
- final broker-review references, not autonomous execution

Design assumptions to bake into the implementation:

- support `client_order_id` for idempotency and traceability
- validate side, quantity, notional, order type, and time in force before prestaging
- keep paper/live environments explicit and impossible to mix accidentally

## What Not To Add Yet

- a browser UI
- direct live order submission after approval
- multi-user auth
- cloud scheduler abstraction
- strategy optimization and backtesting layers

## Confidence

- **High**: Python/FastAPI/Postgres/SQLAlchemy/Alembic fit the existing codebase and target behavior
- **High**: Repo-managed cron plus app-level idempotency is the right local scheduling model
- **Medium**: Exact Quiver endpoints and field names need implementation-time verification against the authenticated docs/account tier
- **High**: Alpaca order prestage must remain a broker-review artifact rather than full trade automation

## Sources

- Quiver API landing page: `https://api.quiverquant.com/`
- Quiver public Python package: `https://github.com/Quiver-Quantitative/python-api`
- Alpaca docs: `https://docs.alpaca.markets/`
