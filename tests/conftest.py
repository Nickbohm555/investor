import os
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


os.environ.setdefault("INVESTOR_APP_SECRET", "test-secret")
os.environ.setdefault("INVESTOR_DATABASE_URL", "sqlite+pysqlite:///:memory:")


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
        return create_app()

    return factory
