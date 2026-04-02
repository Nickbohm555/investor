from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Base, RunRecord
from app.db.session import get_session_factory
from app.services.operation_events import OperationEventService


def _build_service(tmp_path, *, secrets: list[str] | None = None) -> tuple[OperationEventService, object]:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'operation-events.db'}"
    session_factory = get_session_factory(database_url)
    Base.metadata.create_all(bind=session_factory.kw["bind"])
    with Session(session_factory.kw["bind"]) as session:
        session.add(
            RunRecord(
                run_id="run-ops-001",
                status="triggered",
                trigger_source="scheduled",
                approval_status="pending",
                current_step="research",
                state_payload=None,
            )
        )
        session.commit()

    return OperationEventService(session_factory, secrets=secrets or _default_secrets()), session_factory


def _default_secrets() -> list[str]:
    settings = Settings()
    return [
        settings.app_secret,
        settings.smtp_password,
        settings.scheduled_trigger_token,
        settings.execution_trigger_token,
        settings.quiver_api_key,
        settings.openai_api_key,
        settings.alpaca_api_key,
    ]


def test_record_operation_event_persists_stage_provider_outcome_and_codes(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)

    persisted = service.record_event(
        run_id="run-ops-001",
        stage="quiver.fetch",
        provider="quiver",
        outcome="failure",
        error_code="HTTPStatusError",
        http_status=401,
        detail="GET /beta/live/congresstrading",
        trace_id="trace-quiver-401",
    )

    with Session(session_factory.kw["bind"]) as session:
        stored = session.get(type(persisted), persisted.id)

    assert stored is not None
    assert stored.run_id == "run-ops-001"
    assert stored.stage == "quiver.fetch"
    assert stored.provider == "quiver"
    assert stored.outcome == "failure"
    assert stored.error_code == "HTTPStatusError"
    assert stored.http_status == 401
    assert stored.trace_id == "trace-quiver-401"


def test_record_operation_event_masks_secret_values_in_detail(tmp_path) -> None:
    secrets = [
        "smtp-password",
        "change-me-scheduled-trigger",
        "replace-with-openai-api-key",
    ]
    service, session_factory = _build_service(tmp_path, secrets=secrets)

    persisted = service.record_event(
        run_id="run-ops-001",
        stage="smtp.send",
        provider="smtp",
        outcome="failure",
        detail=(
            "smtp-password failed for token change-me-scheduled-trigger "
            "using replace-with-openai-api-key"
        ),
    )

    with Session(session_factory.kw["bind"]) as session:
        stored = session.get(type(persisted), persisted.id)

    assert stored is not None
    assert stored.detail == (
        "***redacted*** failed for token ***redacted*** using ***redacted***"
    )


def test_list_run_events_returns_newest_first(tmp_path) -> None:
    service, _ = _build_service(tmp_path)

    first = service.record_event(
        run_id="run-ops-001",
        stage="quiver.fetch",
        provider="quiver",
        outcome="success",
    )
    second = service.record_event(
        run_id="run-ops-001",
        stage="llm.complete",
        provider="openai",
        outcome="success",
    )

    events = service.list_run_events("run-ops-001")

    assert [event.id for event in events] == [second.id, first.id]

