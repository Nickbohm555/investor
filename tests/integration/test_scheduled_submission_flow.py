from urllib.parse import urlsplit

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import RunRecord
from tests.integration.test_broker_prestage import StubAlpacaClient


class MailProviderSpy:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


class RecordingAlpacaClient(StubAlpacaClient):
    def __init__(self, *, account: dict, asset: dict) -> None:
        super().__init__(account=account, asset=asset)
        self.submitted_orders: list[dict[str, object]] = []

    def submit_order(self, **kwargs) -> dict:
        self.submitted_orders.append(kwargs)
        return {
            "id": f"order-{len(self.submitted_orders)}",
            "client_order_id": kwargs["client_order_id"],
            "status": "accepted",
        }


def _build_restart_safe_apps(app_factory, tmp_path, *, account: dict, asset: dict):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
    alpaca_client = RecordingAlpacaClient(account=account, asset=asset)
    first_app = app_factory(
        database_url=database_url,
        mail_provider=MailProviderSpy(),
        alpaca_client_factory=lambda broker_mode: alpaca_client,
    )
    second_app = app_factory(
        database_url=database_url,
        mail_provider=MailProviderSpy(),
        alpaca_client_factory=lambda broker_mode: alpaca_client,
    )
    return first_app, second_app, alpaca_client


def _execute_headers(app) -> dict[str, str]:
    return {"X-Investor-Execution-Trigger": app.state.settings.execution_trigger_token}


def test_scheduled_trigger_to_submitted_order_flow(
    app_factory,
    tmp_path,
    mock_alpaca_account,
    mock_alpaca_asset,
):
    first_app, second_app, alpaca_client = _build_restart_safe_apps(
        app_factory,
        tmp_path,
        account=mock_alpaca_account,
        asset=mock_alpaca_asset,
    )
    first_client = TestClient(first_app)
    trigger_response = first_client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": first_app.state.settings.scheduled_trigger_token},
    )

    assert trigger_response.status_code == 202
    run_id = trigger_response.json()["run_id"]
    approval_url = first_app.state.mail_provider.sent_messages[-1]["text_body"].split("Approve: ", 1)[1].splitlines()[0].strip()

    second_client = TestClient(second_app)
    approval_response = second_client.get(urlsplit(approval_url).path)
    execute_response = second_client.post(f"/runs/{run_id}/execute", headers=_execute_headers(second_app))

    assert approval_response.status_code == 200
    assert execute_response.status_code == 200
    assert execute_response.json() == {
        "status": "submitted",
        "run_id": run_id,
        "submitted_order_count": 1,
    }

    with Session(second_app.state.session_factory.kw["bind"]) as session:
        stored_run = session.get(RunRecord, run_id)

    assert stored_run is not None
    assert stored_run.status == "submitted"
    assert stored_run.current_step == "submitted"
    assert stored_run.state_payload["submitted_order_count"] == 1
    assert stored_run.state_payload["submitted_orders"]
    assert len(alpaca_client.submitted_orders) == 1


def test_duplicate_scheduled_trigger_does_not_resubmit_orders(
    app_factory,
    tmp_path,
    mock_alpaca_account,
    mock_alpaca_asset,
):
    mail_provider = MailProviderSpy()
    alpaca_client = RecordingAlpacaClient(account=mock_alpaca_account, asset=mock_alpaca_asset)
    app = app_factory(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'investor.db'}",
        mail_provider=mail_provider,
        alpaca_client_factory=lambda broker_mode: alpaca_client,
    )
    client = TestClient(app)

    first_trigger = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": app.state.settings.scheduled_trigger_token},
    )
    run_id = first_trigger.json()["run_id"]
    approval_url = mail_provider.sent_messages[-1]["text_body"].split("Approve: ", 1)[1].splitlines()[0].strip()

    approval_response = client.get(urlsplit(approval_url).path)
    first_execute = client.post(f"/runs/{run_id}/execute", headers=_execute_headers(app))
    duplicate_trigger = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": app.state.settings.scheduled_trigger_token},
    )

    assert approval_response.status_code == 200
    assert first_execute.status_code == 200
    assert duplicate_trigger.status_code == 200
    assert duplicate_trigger.json()["status"] == "duplicate"
    assert len(alpaca_client.submitted_orders) == first_execute.json()["submitted_order_count"]
