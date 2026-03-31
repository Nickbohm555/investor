# Research Summary: Investor

**Date:** 2026-03-31

## Stack

Stay on Python 3.12, FastAPI, Postgres, SQLAlchemy, Alembic, and move the current orchestration to a durable LangGraph-style runtime. Use repo-managed cron for scheduling and a provider-based email service with SMTP implemented first. Keep Quiver and Alpaca behind typed `httpx` adapters and add structured logging plus dry-run verification around the end-to-end flow.

## Table Stakes

- durable daily workflow with restart-safe approval
- broad Quiver research coverage with detailed evidence
- signed expiring approval links in real emails
- no-action/watchlist output when evidence is weak
- deterministic risk and broker policy layers
- pre-staged Alpaca order proposals for final confirmation
- repo-owned cron setup and one-command operational verification

## Architecture Direction

Build around a clean flow: cron trigger -> durable workflow -> Quiver research -> deterministic ranking -> email -> approval resume -> broker prestage -> audit/finalize. The workflow runtime and persistence foundation need to come first because scheduling, approval correctness, and broker safety all depend on durable state and idempotency.

## Watch Out For

- public Quiver examples may not match authenticated endpoint details exactly
- duplicate cron runs can cause duplicate emails or duplicate broker artifacts
- approval flows often appear to work until restart, expiration, or double-click scenarios are tested
- Alpaca paper/live separation and asset/order constraints need explicit guardrails

## Recommendation

Plan the project as a brownfield completion effort with phases centered on:
1. durable workflow and persistence
2. research/data and prompt depth
3. scheduling and email delivery
4. HITL plus broker prestage
5. operational hardening and final readiness

## Sources

- Quiver API: `https://api.quiverquant.com/`
- Quiver Python package: `https://github.com/Quiver-Quantitative/python-api`
- Alpaca docs: `https://docs.alpaca.markets/`
