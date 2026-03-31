# Integrations

## Database

- Local development expects Postgres 16 via `docker-compose.yml`.
- Application code can also run against SQLite through `app/config.py` and test fixtures in `tests/conftest.py`.
- ORM models are defined in `app/db/models.py`.
- Session creation is wrapped by `get_engine`, `get_session_factory`, and `get_db_session` in `app/db/session.py`.

## Quiver

- External Quiver access is represented by `QuiverClient` in `app/tools/quiver.py`.
- Authentication uses an `X-API-Key` header.
- The only implemented endpoint is `GET /congresstrading`.
- The response is mapped into a typed `CongressTrade` model.
- Tests mock the HTTP transport in `tests/tools/test_clients.py`.

## Alpaca

- External Alpaca access is represented by `AlpacaClient` in `app/tools/alpaca.py`.
- Authentication uses `Authorization: Bearer <api_key>`.
- The only implemented endpoint is `GET /v2/account`.
- The current client only extracts `buying_power`.
- Tests mock the HTTP transport in `tests/tools/test_clients.py`.

## Email

- Email composition is implemented in `app/services/email.py`.
- Delivery is currently a no-op console-style stub: `send_console_email` returns the message instead of sending through SMTP or an API provider.
- Approval and rejection URLs are passed into the composer by the workflow layer.

## Approval Tokens

- Approval links are signed and verified with `itsdangerous.URLSafeTimedSerializer` in `app/services/tokens.py`.
- Token payload contains:
  - `run_id`
  - `decision`
  - `issued_at`
- Validation maps bad signatures and expired signatures into local domain exceptions.

## Internal Workflow Boundary

- `app/graph/workflow.py` is the integration point between:
  - research node output
  - risk filtering
  - email composition
  - handoff generation
- The current implementation is an in-process Python class, not a separate workflow engine integration.

## Missing Integrations

- No scheduler exists for daily runs.
- No real email provider is configured.
- No webhook receiver or public callback setup exists beyond the raw FastAPI route.
- No real persistence path connects workflow execution to the SQLAlchemy models.
- No LangGraph checkpoint or durable workflow runtime is integrated despite the product docs calling for it.
