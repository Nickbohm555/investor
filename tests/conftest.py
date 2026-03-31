import os
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.session import get_session_factory
from app.main import create_app


os.environ.setdefault("INVESTOR_APP_SECRET", "test-secret")
os.environ.setdefault("INVESTOR_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("INVESTOR_SCHEDULED_TRIGGER_TOKEN", "test-scheduled-token")
os.environ.setdefault("INVESTOR_SCHEDULE_TRIGGER_URL", "http://127.0.0.1:8000/runs/trigger/scheduled")
os.environ.setdefault("INVESTOR_CRON_LOG_PATH", "logs/cron/daily-trigger.log")
os.environ.setdefault("INVESTOR_SMTP_HOST", "smtp.example.com")
os.environ.setdefault("INVESTOR_SMTP_PORT", "587")
os.environ.setdefault("INVESTOR_SMTP_USERNAME", "investor-user")
os.environ.setdefault("INVESTOR_SMTP_PASSWORD", "change-me")
os.environ.setdefault("INVESTOR_SMTP_FROM_EMAIL", "investor@example.com")
os.environ.setdefault("INVESTOR_DAILY_MEMO_TO_EMAIL", "operator@example.com")
os.environ.setdefault("INVESTOR_EXTERNAL_BASE_URL", "https://investor.example.com")
os.environ.setdefault("INVESTOR_BROKER_MODE", "paper")
os.environ.setdefault("INVESTOR_ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
os.environ.setdefault("INVESTOR_ALPACA_API_KEY", "alpaca-test-key")


class MailProviderSpy:
    def __init__(self) -> None:
        self.sent_messages = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


class StubAlpacaClient:
    def __init__(self) -> None:
        self._account = {"buying_power": "1000.00", "trading_blocked": False}
        self._asset = {"symbol": "NVDA", "tradable": True, "fractionable": True}

    def get_account(self) -> dict:
        return self._account

    def get_asset(self, symbol: str) -> dict:
        assert symbol == "NVDA"
        return self._asset


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def app_factory(tmp_path, monkeypatch):
    def factory(
        *,
        database_url: Optional[str] = None,
        checkpointer_url: Optional[str] = None,
        approval_token_ttl_seconds: int = 900,
        mail_provider=None,
        alpaca_client_factory=None,
    ):
        resolved_database_url = database_url or f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
        monkeypatch.setenv("INVESTOR_DATABASE_URL", resolved_database_url)
        monkeypatch.setenv(
            "INVESTOR_APPROVAL_TOKEN_TTL_SECONDS",
            str(approval_token_ttl_seconds),
        )
        if checkpointer_url is None:
            monkeypatch.delenv("INVESTOR_LANGGRAPH_CHECKPOINTER_URL", raising=False)
        else:
            monkeypatch.setenv("INVESTOR_LANGGRAPH_CHECKPOINTER_URL", checkpointer_url)
        session_factory = get_session_factory(resolved_database_url)
        Base.metadata.create_all(bind=session_factory.kw["bind"])
        app = create_app(
            session_factory=session_factory,
            mail_provider=mail_provider or MailProviderSpy(),
            alpaca_client_factory=alpaca_client_factory or (lambda broker_mode: StubAlpacaClient()),
        )
        return app

    return factory


@pytest.fixture
def mock_alpaca_account() -> dict:
    return {"buying_power": "1000.00", "trading_blocked": False}


@pytest.fixture
def mock_alpaca_asset() -> dict:
    return {"symbol": "NVDA", "tradable": True, "fractionable": True}


@pytest.fixture
def persisted_run(app_factory):
    app = app_factory(mail_provider=MailProviderSpy())
    client = TestClient(app)
    response = client.post("/runs/trigger")

    assert response.status_code == 202

    run_id = response.json()["run_id"]
    with app.state.session_factory() as session:
        run = app.state.run_service.get_run(run_id)
        assert run is not None
        thread_id = run.thread_id

    return {
        "app": app,
        "client": client,
        "run_id": run_id,
        "thread_id": thread_id,
    }
