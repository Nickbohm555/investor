from __future__ import annotations

from urllib.parse import urlsplit

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import RunRecord
from app.ops.dry_run import MailProviderSpy, StubAlpacaClient


def test_duplicate_scheduled_trigger_does_not_resubmit_orders(
    client: TestClient,
    app_with_runtime: tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient],
) -> None:
    _, session_factory, mail_provider, alpaca_client = app_with_runtime

    trigger_response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": "dry-run-trigger-token"},
    )
    trigger_payload = trigger_response.json()
    run_id = trigger_payload["run_id"]

    memo_text = mail_provider.sent_messages[-1]["text_body"]
    approval_path = urlsplit(memo_text.split("Approve: ", 1)[1].splitlines()[0].strip()).path

    approval_response = client.get(approval_path)
    execute_response = client.post(
        f"/runs/{run_id}/execute",
        headers={"X-Investor-Execution-Trigger": "dry-run-execution-token"},
    )
    duplicate_response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": "dry-run-trigger-token"},
    )

    assert trigger_response.status_code == 202
    assert approval_response.status_code == 200
    assert execute_response.status_code == 200
    assert execute_response.json()["submitted_order_count"] == 1
    assert len(alpaca_client.submitted_orders) == 1

    duplicate_payload = duplicate_response.json()
    assert duplicate_response.status_code == 200
    assert duplicate_payload["status"] == "duplicate"
    assert duplicate_payload["duplicate"] is True

    with Session(session_factory.kw["bind"]) as session:
        stored_run = session.scalar(select(RunRecord).where(RunRecord.run_id == run_id))

    assert stored_run is not None
    assert stored_run.state_payload is not None
    assert stored_run.state_payload["submitted_order_count"] == 1
    assert len(alpaca_client.submitted_orders) == 1
