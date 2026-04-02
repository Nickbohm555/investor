from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.agents.research import ResearchNode
from app.db.models import Base
from app.db.session import get_session_factory
from app.ops.dry_run import (
    MailProviderSpy,
    StubAlpacaClient,
    StubResearchLLM,
    _apply_env_overrides,
    _build_quiver_transport,
    _build_settings,
)


@pytest.fixture
def app_with_runtime(tmp_path: Path) -> tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient]:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'investor.db'}"
    settings = _build_settings(database_url)
    _apply_env_overrides(settings)
    os.environ["INVESTOR_SCHEDULE_TIMEZONE"] = settings.schedule_timezone
    session_factory = get_session_factory(database_url)
    Base.metadata.create_all(bind=session_factory.kw["bind"])
    mail_provider = MailProviderSpy()
    alpaca_client = StubAlpacaClient()
    from app.main import create_app

    app = create_app(
        settings=settings,
        session_factory=session_factory,
        mail_provider=mail_provider,
        research_node=ResearchNode(llm=StubResearchLLM()),
        quiver_transport=_build_quiver_transport(),
        alpaca_client_factory=lambda broker_mode: alpaca_client,
    )
    return app, session_factory, mail_provider, alpaca_client


@pytest.fixture
def client(app_with_runtime: tuple[object, sessionmaker, MailProviderSpy, StubAlpacaClient]) -> TestClient:
    app, _, _, _ = app_with_runtime
    with TestClient(app) as test_client:
        yield test_client
