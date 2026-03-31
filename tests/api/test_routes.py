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
