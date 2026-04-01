from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import BrokerArtifactRecord, RecommendationRecord, RunRecord
from app.services.tokens import sign_approval_token


class RecordingAlpacaClient:
    def __init__(self) -> None:
        self.submitted_orders: list[dict[str, object]] = []
        self.fail_on_call: int | None = None

    def get_account(self) -> dict:
        return {"buying_power": "1000.00", "trading_blocked": False}

    def get_asset(self, symbol: str) -> dict:
        return {"symbol": symbol, "tradable": True, "fractionable": True}

    def submit_order(self, **kwargs) -> dict:
        call_number = len(self.submitted_orders) + 1
        if self.fail_on_call == call_number:
            raise RuntimeError("alpaca submit failed")
        self.submitted_orders.append(kwargs)
        return {
            "id": f"order-{len(self.submitted_orders)}",
            "client_order_id": kwargs["client_order_id"],
            "status": "accepted",
        }


def _approved_run(app_factory, tmp_path):
    alpaca_client = RecordingAlpacaClient()
    app = app_factory(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'investor.db'}",
        alpaca_client_factory=lambda broker_mode: alpaca_client,
    )
    client = TestClient(app)
    trigger_response = client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]
    approve_token = sign_approval_token(
        run_id=run_id,
        decision="approve",
        secret=app.state.settings.app_secret,
        ttl_seconds=app.state.settings.approval_token_ttl_seconds,
    )
    approval_response = client.get(f"/approval/{approve_token}")

    assert approval_response.status_code == 200
    assert approval_response.json() == {"status": "broker_prestaged", "run_id": run_id}
    return app, client, run_id, alpaca_client


def _execute_headers(app) -> dict[str, str]:
    return {"X-Investor-Execution-Trigger": app.state.settings.execution_trigger_token}


def test_execute_run_submits_orders_and_returns_submitted_status(app_factory, tmp_path):
    app, client, run_id, alpaca_client = _approved_run(app_factory, tmp_path)

    response = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))

    assert response.status_code == 200
    assert response.json()["status"] == "submitted"
    assert response.json()["run_id"] == run_id
    assert response.json()["submitted_order_count"] >= 1
    assert len(alpaca_client.submitted_orders) == response.json()["submitted_order_count"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored_run = session.get(RunRecord, run_id)

    assert stored_run is not None
    assert stored_run.status == "submitted"
    assert stored_run.current_step == "submitted"
    assert stored_run.state_payload["submitted_order_count"] >= 1
    assert stored_run.state_payload["submitted_orders"]


def test_execute_run_rejects_non_prestaged_runs(app_factory, tmp_path):
    app = app_factory(database_url=f"sqlite+pysqlite:///{tmp_path / 'investor.db'}")
    client = TestClient(app)
    trigger_response = client.post("/runs/trigger")
    run_id = trigger_response.json()["run_id"]

    response = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))

    assert response.status_code == 409
    assert "broker_prestaged" in response.json()["detail"]


def test_execute_run_requires_valid_execution_header(app_factory, tmp_path):
    app, client, run_id, _ = _approved_run(app_factory, tmp_path)

    missing = client.post(f"/runs/{run_id}/execute")
    wrong = client.post(
        f"/runs/{run_id}/execute",
        headers={"X-Investor-Execution-Trigger": "wrong-token"},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_execute_run_is_idempotent_for_already_submitted_runs(app_factory, tmp_path):
    app, client, run_id, alpaca_client = _approved_run(app_factory, tmp_path)

    first_response = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))
    second_response = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert len(alpaca_client.submitted_orders) == first_response.json()["submitted_order_count"]


def test_execute_run_marks_reconciliation_required_after_partial_submission_failure(app_factory, tmp_path):
    app, client, run_id, alpaca_client = _approved_run(app_factory, tmp_path)

    with Session(app.state.session_factory.kw["bind"]) as session:
        recommendation = RecommendationRecord(
            run_id=run_id,
            ticker="MSFT",
            action="buy",
            rationale="Second recommendation for partial failure coverage",
        )
        session.add(recommendation)
        session.flush()
        session.add(
            BrokerArtifactRecord(
                run_id=run_id,
                recommendation_id=recommendation.id,
                broker_mode="paper",
                symbol="MSFT",
                side="buy",
                order_type="market",
                time_in_force="day",
                qty=None,
                notional="250.00",
                client_order_id=f"{run_id}-{recommendation.id}-paper",
                status="draft_ready",
                policy_snapshot_json={
                    "broker_mode": "paper",
                    "account_buying_power": "1000.00",
                    "asset_tradable": True,
                    "asset_fractionable": True,
                    "order_shape": {"type": "market", "time_in_force": "day"},
                },
            )
        )
        session.commit()

    alpaca_client.fail_on_call = 2

    response = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))

    assert response.status_code == 409
    assert "reconciliation" in response.json()["detail"]

    with Session(app.state.session_factory.kw["bind"]) as session:
        stored_run = session.get(RunRecord, run_id)
        artifacts = (
            session.query(BrokerArtifactRecord)
            .filter(BrokerArtifactRecord.run_id == run_id)
            .order_by(BrokerArtifactRecord.recommendation_id.asc())
            .all()
        )

    assert stored_run is not None
    assert stored_run.status == "broker_prestaged"
    assert stored_run.state_payload["submitted_order_count"] == 1
    assert artifacts[0].status == "submitted"
    assert artifacts[1].status == "submission_in_flight"
