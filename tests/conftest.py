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
        app = create_app(session_factory=session_factory)
        # session_factory override keeps the shared in-memory SQLite harness stable in tests.
        app.state.session_factory = session_factory
        if mail_provider is not None:
            app.state.mail_provider = mail_provider
        return app

    return factory
