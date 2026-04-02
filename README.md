# investor

Local-first Python service for an app-owned investing workflow.

## System Architecture

![System diagram for the investor runtime](docs/architecture/system-diagram.png)

The diagram shows the live operator and automation paths: manual and scheduled triggers enter the FastAPI app, the workflow gathers Quiver evidence, uses the OpenAI-compatible research model, delivers the SMTP memo, and resumes through the approval link. Durable records for runs, recommendations, approval events, state transitions, and broker artifacts stay visible because restart safety is part of the implemented contract.

The current approved path ends at `broker_prestaged`, where broker artifacts are persisted and ready for broker review. The README and diagram intentionally stop there rather than presenting direct order submission as the current architecture. Use `python -m app.ops.dry_run` as the fastest proof path that the trigger, memo, approval, and broker-prestage flow still line up.

## Detailed Flow Diagrams

These step-level diagrams break the runtime into separate, readable stages. Each screenshot has a matching editable `.excalidraw` source in `docs/architecture/flow-steps/`.

### 1. Cron Install + Scheduled Trigger

Editable source: `docs/architecture/flow-steps/01-cron-scheduled-trigger.excalidraw`

![Cron install and scheduled trigger flow](docs/architecture/flow-steps/01-cron-scheduled-trigger.png)

### 2. Scheduled API Ingress + Run Creation

Editable source: `docs/architecture/flow-steps/02-scheduled-api-ingress.excalidraw`

![Scheduled API ingress and run creation flow](docs/architecture/flow-steps/02-scheduled-api-ingress.png)

### 3. Research Agent + Quiver Loop

Editable source: `docs/architecture/flow-steps/03-research-agent-quiver-loop.excalidraw`

![Research agent and Quiver loop flow](docs/architecture/flow-steps/03-research-agent-quiver-loop.png)

### 4. Strategic Report + Email Delivery

Editable source: `docs/architecture/flow-steps/04-report-email-delivery.excalidraw`

![Strategic report and email delivery flow](docs/architecture/flow-steps/04-report-email-delivery.png)

### 5. Approval Callback + Broker Prestage

Editable source: `docs/architecture/flow-steps/05-approval-broker-prestage.excalidraw`

![Approval callback and broker prestage flow](docs/architecture/flow-steps/05-approval-broker-prestage.png)

### 6. Execution Confirmation + Order Submission

Editable source: `docs/architecture/flow-steps/06-execution-order-submission.excalidraw`

![Execution confirmation and order submission flow](docs/architecture/flow-steps/06-execution-order-submission.png)

## Setup

```bash
pip install -e .
cp .env.example .env
docker compose up -d postgres
alembic upgrade head
```

Normal runtime composition now depends on the configured Quiver and OpenAI-compatible credentials rather than the old stubbed defaults.

## Dry Run

```bash
python -m app.ops.dry_run
```

Use `python -m app.ops.dry_run` as the canonical no-hidden-manual-work proof path. It runs scheduled trigger, memo generation, approval callback, and broker prestage locally by injecting deterministic doubles instead of the normal live adapters.

## Run The Service

```bash
uvicorn app.main:app --reload
```

## Cron Operations

```bash
./scripts/cron-install.sh
./scripts/cron-status.sh
./scripts/cron-trigger.sh
./scripts/cron-remove.sh
```

The managed cron contract is a repo-configured `7:00am ET` weekday install. Keep `INVESTOR_SCHEDULE_CRON_EXPRESSION=0 7 * * 1-5` and `INVESTOR_SCHEDULE_TIMEZONE=America/New_York` aligned unless you intentionally want a different cadence. `./scripts/cron-status.sh` prints the active cron expression, timezone, and log path so the installed block matches the repo config.

## Go-Live Checklist

- SMTP credentials send to the real operator inbox
- Quiver API key and base URL point to the intended account
- OpenAI-compatible API key, base URL, and model are configured for ResearchNode
- INVESTOR_EXTERNAL_BASE_URL resolves to the public approval host
- Alpaca paper mode uses https://paper-api.alpaca.markets
- INVESTOR_SCHEDULE_TIMEZONE is set to America/New_York for the managed 7:00am ET cron install
- Cron is installed with ./scripts/cron-install.sh and verified with ./scripts/cron-status.sh

## Acceptance Check

```bash
python -m app.ops.dry_run
```
