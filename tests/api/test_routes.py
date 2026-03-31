from sqlalchemy.orm import Session

from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.tokens import sign_approval_token


def _build_app(tmp_path, monkeypatch):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
    monkeypatch.setenv("INVESTOR_DATABASE_URL", database_url)
    return create_app()


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
    app = _build_app(tmp_path, monkeypatch)
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
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()

    assert updated is not None
    assert updated.thread_id == stored.thread_id
    assert updated.status == "completed"
    assert len(approval_events) == 1
    assert approval_events[0].decision == "approve"


def test_invalid_approval_token_returns_400(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/approval/not-a-real-token")

    assert response.status_code == 400
    assert response.json() == {"detail": "Approval token invalid"}


def test_expired_approval_token_returns_410(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    client.post("/runs/trigger")
    app.state.settings.approval_token_ttl_seconds = -1
    token = sign_approval_token(
        run_id="run-expired",
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 410
    assert response.json() == {"detail": "Approval token expired"}


def test_unknown_run_approval_returns_404(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    token = sign_approval_token(
        run_id="missing-run",
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    response = client.get(f"/approval/{token}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}


def test_duplicate_approval_returns_409_and_keeps_single_event(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    trigger_response = client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    first = client.get(f"/approval/{token}")
    second = client.get(f"/approval/{token}")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json() == {"detail": "Approval already recorded"}

    with Session(app.state.session_factory.kw["bind"]) as session:
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id=run_id).all()

    assert len(approval_events) == 1


def test_stale_approval_returns_409(tmp_path, monkeypatch):
    app = _build_app(tmp_path, monkeypatch)
    client = TestClient(app)
    trigger_response = client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    reject_token = sign_approval_token(
        run_id=run_id,
        decision="reject",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )

    rejected = client.get(f"/approval/{reject_token}")
    stale = client.get(f"/approval/{approve_token}")

    assert rejected.status_code == 200
    assert stale.status_code == 409
    assert stale.json() == {"detail": "Approval already processed"}
