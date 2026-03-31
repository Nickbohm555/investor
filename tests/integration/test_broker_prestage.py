import os

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import BrokerArtifactRecord, RecommendationRecord, RunRecord
from app.services.tokens import sign_approval_token

POSTGRES_SMOKE_DATABASE_URL = "postgresql://investor:investor@localhost:5432/investor"


class MailProviderSpy:
    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        return None


class StubAlpacaClient:
    def __init__(self, *, account: dict, asset: dict) -> None:
        self._account = account
        self._asset = asset

    def get_account(self) -> dict:
        return self._account

    def get_asset(self, symbol: str) -> dict:
        assert symbol == "NVDA"
        return self._asset


def _resolve_database_url(tmp_path) -> str:
    configured_database_url = os.getenv("INVESTOR_DATABASE_URL")
    if configured_database_url and configured_database_url.startswith("postgresql://"):
        return configured_database_url
    return f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"


def _build_restart_safe_apps(app_factory, tmp_path, *, account: dict, asset: dict):
    database_url = _resolve_database_url(tmp_path)
    first_app = app_factory(
        database_url=database_url,
        mail_provider=MailProviderSpy(),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(account=account, asset=asset),
    )
    second_app = app_factory(
        database_url=database_url,
        mail_provider=MailProviderSpy(),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(account=account, asset=asset),
    )
    return first_app, second_app


def test_approved_run_creates_broker_artifacts(app_factory, tmp_path, mock_alpaca_account, mock_alpaca_asset):
    first_app, second_app = _build_restart_safe_apps(
        app_factory,
        tmp_path,
        account=mock_alpaca_account,
        asset=mock_alpaca_asset,
    )
    first_client = TestClient(first_app)
    trigger_response = first_client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=first_app.state.settings.app_secret,
        ttl_seconds=first_app.state.settings.approval_token_ttl_seconds,
    )

    second_client = TestClient(second_app)
    approval_response = second_client.get(f"/approval/{approve_token}")

    assert approval_response.status_code == 200
    assert approval_response.json() == {"status": "broker_prestaged", "run_id": run_id}


def test_broker_artifact_links_to_run_and_recommendations(app_factory, tmp_path, mock_alpaca_account, mock_alpaca_asset):
    first_app, second_app = _build_restart_safe_apps(
        app_factory,
        tmp_path,
        account=mock_alpaca_account,
        asset=mock_alpaca_asset,
    )
    first_client = TestClient(first_app)
    trigger_response = first_client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=first_app.state.settings.app_secret,
        ttl_seconds=first_app.state.settings.approval_token_ttl_seconds,
    )

    TestClient(second_app).get(f"/approval/{approve_token}")

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        run = session.get(RunRecord, run_id)
        recommendations = session.query(RecommendationRecord).filter_by(run_id=run_id).all()
        artifacts = session.query(BrokerArtifactRecord).filter_by(run_id=run_id).all()

    assert run is not None
    assert recommendations
    assert len(artifacts) == len(recommendations)
    assert artifacts[0].recommendation_id == recommendations[0].id
    assert artifacts[0].run_id == run_id
    assert artifacts[0].client_order_id == f"{run_id}-{recommendations[0].id}-paper"


def test_reject_path_creates_no_broker_artifacts(app_factory, tmp_path, mock_alpaca_account, mock_alpaca_asset):
    first_app, second_app = _build_restart_safe_apps(
        app_factory,
        tmp_path,
        account=mock_alpaca_account,
        asset=mock_alpaca_asset,
    )
    first_client = TestClient(first_app)
    trigger_response = first_client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    reject_token = sign_approval_token(
        run_id=run_id,
        decision="reject",
        secret=first_app.state.settings.app_secret,
        ttl_seconds=first_app.state.settings.approval_token_ttl_seconds,
    )

    second_client = TestClient(second_app)
    reject_response = second_client.get(f"/approval/{reject_token}")

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        artifacts = session.query(BrokerArtifactRecord).filter_by(run_id=run_id).all()

    assert reject_response.status_code == 200
    assert reject_response.json() == {"status": "rejected", "run_id": run_id}
    assert artifacts == []


def test_invalid_broker_policy_blocks_artifact_creation(app_factory, tmp_path, mock_alpaca_asset):
    first_app, second_app = _build_restart_safe_apps(
        app_factory,
        tmp_path,
        account={"buying_power": "100.00", "trading_blocked": False},
        asset=mock_alpaca_asset,
    )
    first_client = TestClient(first_app)
    trigger_response = first_client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=first_app.state.settings.app_secret,
        ttl_seconds=first_app.state.settings.approval_token_ttl_seconds,
    )

    second_client = TestClient(second_app)
    approval_response = second_client.get(f"/approval/{approve_token}")

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        artifacts = session.query(BrokerArtifactRecord).filter_by(run_id=run_id).all()

    assert approval_response.status_code == 409
    assert artifacts == []
