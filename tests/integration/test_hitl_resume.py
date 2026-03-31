import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ApprovalEventRecord, RunRecord, StateTransitionRecord
from app.services.approvals import (
    ApprovalService,
    DuplicateApprovalError,
    MissingRunError,
    RunNotAwaitingReviewError,
    StaleApprovalError,
)
from app.services.tokens import ApprovalTokenPayload

POSTGRES_SMOKE_DATABASE_URL = "postgresql://investor:investor@localhost:5432/investor"


class MailProviderSpy:
    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        return None


def _resolve_database_url(tmp_path) -> str:
    configured_database_url = os.getenv("INVESTOR_DATABASE_URL")
    if configured_database_url and configured_database_url.startswith("postgresql://"):
        return configured_database_url
    return f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"


def _create_run_and_payload(app_factory, tmp_path):
    database_url = _resolve_database_url(tmp_path)
    checkpointer_url = os.getenv("INVESTOR_LANGGRAPH_CHECKPOINTER_URL")

    first_app = app_factory(
        database_url=database_url,
        checkpointer_url=checkpointer_url,
        mail_provider=MailProviderSpy(),
    )
    first_app.state.runtime.mail_provider = first_app.state.mail_provider
    first_client = TestClient(first_app)
    trigger_response = first_client.post("/runs/trigger")

    assert trigger_response.status_code == 202

    run_id = trigger_response.json()["run_id"]
    payload = ApprovalTokenPayload(
        run_id=run_id,
        decision="approve",
        token_id="token-approve-1",
    )
    second_app = app_factory(
        database_url=database_url,
        checkpointer_url=checkpointer_url,
        mail_provider=MailProviderSpy(),
    )
    second_app.state.runtime.mail_provider = second_app.state.mail_provider
    return first_app, second_app, run_id, payload


def test_approval_resumes_same_thread(app_factory, tmp_path):
    first_app, second_app, run_id, payload = _create_run_and_payload(app_factory, tmp_path)

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        stored_before = session.get(RunRecord, run_id)

    service = ApprovalService(
        session_factory=second_app.state.session_factory,
        runtime=second_app.state.runtime,
        research_node=second_app.state.research_node,
    )
    result = service.apply_review_decision(payload, token_id=payload.token_id)

    assert stored_before is not None
    assert stored_before.status == "awaiting_review"
    assert result["thread_id"] == stored_before.thread_id
    assert result["status"] == "completed"

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        stored_after = session.get(RunRecord, run_id)
        transitions = (
            session.query(StateTransitionRecord)
            .filter_by(run_id=run_id)
            .order_by(StateTransitionRecord.id.asc())
            .all()
        )

    assert stored_after is not None
    assert stored_after.thread_id == stored_before.thread_id
    assert [transition.to_status for transition in transitions] == [
        "awaiting_review",
        "resuming",
        "completed",
    ]


def test_reject_finalizes_without_broker_side_effects(app_factory, tmp_path):
    _, second_app, run_id, payload = _create_run_and_payload(app_factory, tmp_path)
    payload = ApprovalTokenPayload(
        run_id=run_id,
        decision="reject",
        token_id="token-reject-1",
    )
    broker_calls: list[tuple[str, tuple[int, ...], str]] = []

    service = ApprovalService(
        session_factory=second_app.state.session_factory,
        runtime=second_app.state.runtime,
        research_node=second_app.state.research_node,
        prestage_service=lambda run_id, recommendation_ids, broker_mode: broker_calls.append(
            (run_id, tuple(recommendation_ids), broker_mode)
        ),
    )
    result = service.apply_review_decision(payload, token_id=payload.token_id)

    assert result == {"run_id": run_id, "status": "rejected"}
    assert broker_calls == []

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        run = session.get(RunRecord, run_id)
        events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()

    assert run is not None
    assert run.status == "rejected"
    assert len(events) == 1
    assert events[0].decision == "reject"


def test_duplicate_approval_returns_explicit_error(app_factory, tmp_path):
    _, second_app, run_id, payload = _create_run_and_payload(app_factory, tmp_path)
    service = ApprovalService(
        session_factory=second_app.state.session_factory,
        runtime=second_app.state.runtime,
        research_node=second_app.state.research_node,
    )

    first = service.apply_review_decision(payload, token_id=payload.token_id)

    assert first["status"] == "completed"

    with pytest.raises(DuplicateApprovalError):
        service.apply_review_decision(payload, token_id=payload.token_id)

    stale_payload = ApprovalTokenPayload(
        run_id=run_id,
        decision="reject",
        token_id="token-reject-after-approve",
    )
    with pytest.raises(StaleApprovalError):
        service.apply_review_decision(stale_payload, token_id=stale_payload.token_id)


def test_stale_or_missing_run_returns_explicit_error(app_factory, tmp_path):
    _, second_app, run_id, _ = _create_run_and_payload(app_factory, tmp_path)
    service = ApprovalService(
        session_factory=second_app.state.session_factory,
        runtime=second_app.state.runtime,
        research_node=second_app.state.research_node,
    )

    with pytest.raises(MissingRunError):
        service.apply_review_decision(
            ApprovalTokenPayload(
                run_id="missing-run",
                decision="approve",
                token_id="missing-token",
            ),
            token_id="missing-token",
        )

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        run = session.get(RunRecord, run_id)
        assert run is not None
        run.status = "completed"
        session.commit()

    with pytest.raises(StaleApprovalError):
        service.apply_review_decision(
            ApprovalTokenPayload(
                run_id=run_id,
                decision="approve",
                token_id="stale-token",
            ),
            token_id="stale-token",
        )

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        run = session.get(RunRecord, run_id)
        assert run is not None
        run.status = "resuming"
        session.commit()

    with pytest.raises(RunNotAwaitingReviewError):
        service.apply_review_decision(
            ApprovalTokenPayload(
                run_id=run_id,
                decision="approve",
                token_id="not-awaiting-review",
            ),
            token_id="not-awaiting-review",
        )
