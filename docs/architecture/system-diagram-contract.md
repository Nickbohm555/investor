# System Diagram Contract

This file is the source-of-truth inventory and layout contract for the editable architecture diagram in `docs/architecture/system-diagram.excalidraw`.

## Scope Boundary

- Diagram only the implemented operator and runtime path from trigger through `broker_prestaged`.
- The truthful approved-path terminal state is `broker_prestaged`.
- Direct order submission is not part of the current diagram.
- Do not show LangGraph or checkpointing as current behavior.

## Lane Order

1. Operator
2. Automation
3. Application Runtime
4. External Services
5. Storage

## Lanes

### Operator

- Manual trigger
  - Role: operator starts an on-demand run through `/runs/trigger`.
- Approval callback
  - Role: operator clicks the memo approval link that resolves to `/approval/{token}`.
- Proof paths
  - `python -m app.ops.dry_run`
  - `./scripts/cron-install.sh`
  - `./scripts/cron-trigger.sh`

### Automation

- Scheduled trigger
  - Role: repo-managed cron calls the scheduled route through `/runs/trigger/scheduled`.
- Cron installer
  - Role: installs the weekday schedule that invokes `./scripts/cron-trigger.sh`.
- Cron trigger script
  - Role: posts to the scheduled route and logs started or duplicate outcomes.

### Application Runtime

- FastAPI app
  - Role: application entrypoint from `app.main.py` that mounts the API routes and runtime services.
- `/runs/trigger`
  - Role: manual trigger route that creates a pending run and starts the workflow.
- `/runs/trigger/scheduled`
  - Role: scheduled trigger route with duplicate protection.
- `/approval/{token}`
  - Role: approval service route that validates the signed token and applies the review decision.
- WorkflowEngine
  - Role: persisted application-owned workflow coordinator.
- ResearchNode
  - Role: bounded research agent used by the workflow.
- compose_report_email
  - Role: memo/report composition step before SMTP delivery.
- Approval service
  - Role: token validation plus durable approval decision handling.
- BrokerPrestageService
  - Role: create persisted broker artifacts for approved recommendations.
- broker_prestaged
  - Role: current approved-path terminal state and runtime boundary for this diagram.

### External Services

- Quiver
  - Role: source of congress, insider, contract, and lobbying evidence.
- OpenAI-compatible LLM
  - Role: model backend used by `ResearchNode`.
- SMTP
  - Role: daily memo delivery transport.
- Alpaca
  - Role: current-state broker touchpoint after persisted broker artifacts exist.

### Storage

- runs
  - Role: durable run state, trigger source, and persisted workflow payload.
- recommendations
  - Role: finalized recommendation rows attached to a run.
- approval_events
  - Role: durable token decision audit log.
- state_transitions
  - Role: workflow status transition history.
- broker_artifacts
  - Role: persisted broker handoff records created after approval.

## Required Edges

- Manual trigger -> FastAPI app
- Scheduled trigger -> FastAPI app
- Approval callback -> approval service
- WorkflowEngine -> Quiver
- WorkflowEngine -> OpenAI-compatible LLM
- WorkflowEngine -> SMTP memo
- WorkflowEngine -> runs/recommendations/approval_events/state_transitions
- broker_prestaged -> broker_artifacts -> Alpaca

## Diagram Layout Rules

- Keep the five lane headers in this exact order: Operator, Automation, Application Runtime, External Services, Storage.
- Use separate ingress arrows for Manual trigger, Scheduled trigger, and Approval callback before they merge into the shared runtime lane.
- Show FastAPI app above the route boxes so ingress can enter one service boundary before flowing into the route-specific behavior.
- Show WorkflowEngine as the central runtime coordinator with nearby boxes for ResearchNode, compose_report_email, Approval service, BrokerPrestageService, and broker_prestaged.
- Place Quiver, OpenAI-compatible LLM, SMTP, and Alpaca in the External Services lane with arrows returning to or from the runtime lane as listed above.
- Place runs, recommendations, approval_events, state_transitions, and broker_artifacts in the Storage lane with enough spacing that each durable record is readable in the exported screenshot.
- Add a small boxed proof-path note listing `python -m app.ops.dry_run`, `./scripts/cron-install.sh`, and `./scripts/cron-trigger.sh`.
- Keep the visual language current-state only. Do not show direct submitted-order flow.

## Proof Paths

- `python -m app.ops.dry_run` proves the operator-visible flow across scheduled trigger, memo generation, approval callback, and broker prestage.
- `./scripts/cron-install.sh` proves the repo-owned schedule install path.
- `./scripts/cron-trigger.sh` proves the scheduled ingress path into the FastAPI app.
