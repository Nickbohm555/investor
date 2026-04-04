from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import RecommendationRecord, RunRecord
from app.ops.dry_run import MailProviderSpy, StubAlpacaClient


def test_manual_trigger_sends_one_memo_and_persists_awaiting_review_state(
    client: TestClient,
    app_with_runtime: tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient],
) -> None:
    _, session_factory, mail_provider, _ = app_with_runtime

    response = client.post("/runs/trigger")
    payload = response.json()

    assert response.status_code == 202
    assert len(mail_provider.sent_messages) == 1
    assert mail_provider.sent_messages[0]["recipient"] == "operator@test.local"

    with Session(session_factory.kw["bind"]) as session:
        stored_run = session.scalar(select(RunRecord).where(RunRecord.run_id == payload["run_id"]))
        stored_recommendations = session.scalars(
            select(RecommendationRecord).where(RecommendationRecord.run_id == payload["run_id"])
        ).all()

    assert stored_run is not None
    assert stored_run.status == "awaiting_review"
    assert stored_run.current_step == "awaiting_review"
    assert stored_run.state_payload is not None
    assert stored_run.state_payload["status"] == "awaiting_review"
    assert stored_run.state_payload["current_step"] == "awaiting_review"
    assert len(stored_recommendations) == 1

