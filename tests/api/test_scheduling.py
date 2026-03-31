import logging

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.models import RunRecord


class MailProviderSpy:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.sent_messages = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        if self.should_fail:
            raise RuntimeError("smtp send failed")
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


def _build_client(app_factory, *, mail_provider=None) -> tuple[TestClient, object]:
    app = app_factory(database_url="sqlite+pysqlite:///:memory:", mail_provider=mail_provider)
    return TestClient(app), app


def test_scheduled_trigger_with_valid_header_creates_daily_run(app_factory, caplog):
    mail_provider = MailProviderSpy()
    client, app = _build_client(app_factory, mail_provider=mail_provider)
    caplog.set_level(logging.INFO)

    response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": app.state.settings.scheduled_trigger_token},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "started"
    assert payload["duplicate"] is False
    assert payload["schedule_key"].startswith("daily:")
    assert len(mail_provider.sent_messages) == 1
    assert "scheduled_trigger result=started" in caplog.text
    assert f"schedule_key={payload['schedule_key']}" in caplog.text
    assert f"run_id={payload['run_id']}" in caplog.text

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, payload["run_id"])

    assert stored is not None
    assert stored.schedule_key == payload["schedule_key"]
    assert stored.trigger_source == "scheduled"


def test_scheduled_trigger_duplicate_returns_original_run(app_factory, caplog):
    mail_provider = MailProviderSpy()
    client, app = _build_client(app_factory, mail_provider=mail_provider)
    headers = {"X-Investor-Scheduled-Trigger": app.state.settings.scheduled_trigger_token}
    caplog.set_level(logging.INFO)

    first = client.post("/runs/trigger/scheduled", headers=headers)
    second = client.post("/runs/trigger/scheduled", headers=headers)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert second.json()["duplicate"] is True
    assert second.json()["run_id"] == first.json()["run_id"]
    assert second.json()["schedule_key"] == first.json()["schedule_key"]
    assert len(mail_provider.sent_messages) == 1
    assert "scheduled_trigger result=duplicate" in caplog.text

    with Session(app.state.session_factory.kw["bind"]) as session:
        run_ids = session.scalars(select(RunRecord.run_id)).all()

    assert len(run_ids) == 1


def test_scheduled_trigger_requires_valid_header(app_factory):
    client, app = _build_client(app_factory)

    missing = client.post("/runs/trigger/scheduled")
    wrong = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": "wrong-token"},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401

    with Session(app.state.session_factory.kw["bind"]) as session:
        run_ids = session.scalars(select(RunRecord.run_id)).all()

    assert run_ids == []


def test_scheduled_trigger_logs_failure_when_mail_delivery_raises(app_factory, caplog):
    mail_provider = MailProviderSpy(should_fail=True)
    client, app = _build_client(app_factory, mail_provider=mail_provider)
    caplog.set_level(logging.INFO)

    response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": app.state.settings.scheduled_trigger_token},
    )

    assert response.status_code == 500
    assert "scheduled_trigger result=failure" in caplog.text
