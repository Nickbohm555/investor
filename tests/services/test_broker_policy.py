from types import SimpleNamespace

import pytest

from app.db.models import Base
from app.db.session import get_session_factory
from app.schemas.broker import BrokerMode
from app.schemas.workflow import Recommendation
from app.services.broker_policy import BrokerPolicyError
from app.services.broker_prestage import BrokerPrestageService
from app.services.run_service import RunService


class StubAlpacaClient:
    def __init__(self, *, account: dict, asset: dict) -> None:
        self._account = account
        self._asset = asset

    def get_account(self) -> dict:
        return self._account

    def get_asset(self, symbol: str) -> dict:
        assert symbol == "NVDA"
        return self._asset


def _seed_run_and_recommendation():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    run_service = RunService(session_factory)
    run_service.create_pending_run(
        run_id="run-123",
        status="awaiting_review",
        current_step="awaiting_review",
        trigger_source="manual",
    )
    recommendation = run_service.store_recommendations(
        "run-123",
        [
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.82,
                rationale="Durable infrastructure demand remains strong.",
            )
        ],
    )[0]
    return session_factory, recommendation.id


def test_rejects_unsupported_mode():
    session_factory, recommendation_id = _seed_run_and_recommendation()
    service = BrokerPrestageService(
        session_factory=session_factory,
        settings=SimpleNamespace(
            broker_mode="paper",
            alpaca_base_url="https://paper-api.alpaca.markets",
        ),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(
            account={"buying_power": "1000.00", "trading_blocked": False},
            asset={"tradable": True, "fractionable": True},
        ),
    )

    with pytest.raises(BrokerPolicyError):
        service.prestage_approved_recommendations(
            run_id="run-123",
            recommendation_ids=[recommendation_id],
            broker_mode="sandbox",
        )


def test_rejects_non_tradable_asset():
    session_factory, recommendation_id = _seed_run_and_recommendation()
    service = BrokerPrestageService(
        session_factory=session_factory,
        settings=SimpleNamespace(
            broker_mode="paper",
            alpaca_base_url="https://paper-api.alpaca.markets",
        ),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(
            account={"buying_power": "1000.00", "trading_blocked": False},
            asset={"tradable": False, "fractionable": True},
        ),
    )

    with pytest.raises(BrokerPolicyError):
        service.prestage_approved_recommendations(
            run_id="run-123",
            recommendation_ids=[recommendation_id],
            broker_mode="paper",
        )


def test_rejects_insufficient_buying_power():
    session_factory, recommendation_id = _seed_run_and_recommendation()
    service = BrokerPrestageService(
        session_factory=session_factory,
        settings=SimpleNamespace(
            broker_mode="paper",
            alpaca_base_url="https://paper-api.alpaca.markets",
        ),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(
            account={"buying_power": "100.00", "trading_blocked": False},
            asset={"tradable": True, "fractionable": True},
        ),
    )

    with pytest.raises(BrokerPolicyError):
        service.prestage_approved_recommendations(
            run_id="run-123",
            recommendation_ids=[recommendation_id],
            broker_mode="paper",
        )


def test_prestages_supported_market_buy():
    session_factory, recommendation_id = _seed_run_and_recommendation()
    service = BrokerPrestageService(
        session_factory=session_factory,
        settings=SimpleNamespace(
            broker_mode="paper",
            alpaca_base_url="https://paper-api.alpaca.markets",
        ),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(
            account={"buying_power": "1000.00", "trading_blocked": False},
            asset={"tradable": True, "fractionable": True},
        ),
    )

    artifacts = service.prestage_approved_recommendations(
        run_id="run-123",
        recommendation_ids=[recommendation_id],
        broker_mode="paper",
    )

    assert len(artifacts) == 1
    assert artifacts[0].broker_mode == BrokerMode.paper
    assert artifacts[0].client_order_id == "run-123-1-paper"


def test_uses_configured_broker_mode():
    session_factory, recommendation_id = _seed_run_and_recommendation()
    service = BrokerPrestageService(
        session_factory=session_factory,
        settings=SimpleNamespace(
            broker_mode="live",
            alpaca_base_url="https://api.alpaca.markets",
        ),
        alpaca_client_factory=lambda broker_mode: StubAlpacaClient(
            account={"buying_power": "1000.00", "trading_blocked": False},
            asset={"tradable": True, "fractionable": True},
        ),
    )

    artifacts = service.prestage_approved_recommendations(
        run_id="run-123",
        recommendation_ids=[recommendation_id],
        broker_mode="live",
    )

    assert artifacts[0].broker_mode == BrokerMode.live
    assert artifacts[0].client_order_id == "run-123-1-live"
