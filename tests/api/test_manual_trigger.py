from __future__ import annotations

import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import RunRecord
from app.ops.dry_run import MailProviderSpy, StubAlpacaClient


def test_manual_trigger_returns_started_payload_and_persists_manual_source(
    client: TestClient,
    app_with_runtime: tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient],
) -> None:
    _, session_factory, _, _ = app_with_runtime

    response = client.post("/runs/trigger")
    payload = response.json()

    assert response.status_code == 202
    assert payload["status"] == "started"
    assert re.fullmatch(r"run-[0-9a-f]{8}", payload["run_id"])

    with Session(session_factory.kw["bind"]) as session:
        stored_run = session.scalar(select(RunRecord).where(RunRecord.run_id == payload["run_id"]))

    assert stored_run is not None
    assert stored_run.trigger_source == "manual"


def test_manual_trigger_failure_returns_created_run_id(
    client: TestClient,
    app_with_runtime: tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient],
) -> None:
    app, session_factory, _, _ = app_with_runtime

    def fail_start_run(*, run_id: str, quiver_client: object, baseline_report: dict | None = None) -> dict:
        _ = quiver_client
        _ = baseline_report
        raise RuntimeError("manual-start failed")

    app.state.runtime.workflow_engine.start_run = fail_start_run

    response = client.post("/runs/trigger")
    payload = response.json()

    assert response.status_code == 500
    assert payload["detail"]["message"] == "Manual trigger failed"
    assert re.fullmatch(r"run-[0-9a-f]{8}", payload["detail"]["run_id"])

    with Session(session_factory.kw["bind"]) as session:
        stored_run = session.scalar(select(RunRecord).where(RunRecord.run_id == payload["detail"]["run_id"]))

    assert stored_run is not None
    assert stored_run.trigger_source == "manual"

