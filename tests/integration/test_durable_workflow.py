import os

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    ApprovalEventRecord,
    RecommendationRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.services.tokens import sign_approval_token

POSTGRES_SMOKE_DATABASE_URL = "postgresql://investor:investor@localhost:5432/investor"


def test_durable_workflow_survives_app_restart(app_factory, tmp_path):
    configured_database_url = os.getenv("INVESTOR_DATABASE_URL")
    if configured_database_url and configured_database_url.startswith("postgresql://"):
        database_url = configured_database_url
    else:
        database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"

    # Build create_app() twice against the same database URL to prove restart safety.
    first_app = app_factory(
        database_url=database_url,
    )
    first_client = TestClient(first_app)

    trigger_response = first_client.post("/runs/trigger")

    assert trigger_response.status_code == 202
    run_id = trigger_response.json()["run_id"]
    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=first_app.state.settings.app_secret,
        ttl_seconds=first_app.state.settings.approval_token_ttl_seconds,
    )

    second_app = app_factory(
        database_url=database_url,
    )
    second_client = TestClient(second_app)
    approval_response = second_client.get(f"/approval/{token}")
    duplicate_response = second_client.get(f"/approval/{token}")

    assert approval_response.status_code == 200
    assert approval_response.json() == {"status": "broker_prestaged", "run_id": run_id}
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "Approval already recorded"}

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        run = session.get(RunRecord, run_id)
        recommendations = session.query(RecommendationRecord).filter_by(run_id=run_id).all()
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()
        transitions = session.query(StateTransitionRecord).filter_by(run_id=run_id).all()

    assert run is not None
    assert run.status == "broker_prestaged"
    assert len(recommendations) >= 1
    assert len(approval_events) == 1
    assert {transition.to_status for transition in transitions} >= {
        "awaiting_review",
        "broker_prestaged",
    }
