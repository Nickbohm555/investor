from sqlalchemy.orm import Session

from app.db.models import RecommendationRecord, RunRecord
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.tokens import sign_approval_token


def test_app_starts_with_test_settings():
    app = create_app()

    assert app is not None


def test_health_route_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_manual_trigger_starts_a_run():
    client = TestClient(create_app())

    response = client.post("/runs/trigger")

    assert response.status_code == 202
    assert response.json()["status"] == "started"


def test_approval_callback_resumes_a_paused_run():
    app = create_app()
    client = TestClient(app)

    trigger_response = client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=900,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_trigger_persists_run_and_approval_reuses_same_thread(tmp_path, monkeypatch):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
    monkeypatch.setenv("INVESTOR_DATABASE_URL", database_url)
    app = create_app()
    client = TestClient(app)

    trigger_response = client.post("/runs/trigger")

    assert trigger_response.status_code == 202
    run_id = trigger_response.json()["run_id"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored = session.get(RunRecord, run_id)
        recommendations = session.query(RecommendationRecord).filter_by(run_id=run_id).all()

    assert stored is not None
    assert stored.thread_id
    assert stored.status == "awaiting_human_review"
    assert recommendations
    assert not hasattr(app.state, "workflow_store")

    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )
    approval_response = client.get(f"/approval/{token}")

    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "completed"

    with Session(app.state.session_factory.kw["bind"]) as session:
        updated = session.get(RunRecord, run_id)

    assert updated is not None
    assert updated.thread_id == stored.thread_id
    assert updated.status == "completed"
