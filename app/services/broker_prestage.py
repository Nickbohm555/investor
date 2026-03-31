from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import RecommendationRecord
from app.repositories.broker_artifacts import BrokerArtifactsRepository
from app.schemas.broker import BrokerArtifact, BrokerMode, OrderProposal
from app.services.broker_policy import BrokerPolicyError, validate_order_proposal
from app.tools.alpaca import AlpacaClient

DEFAULT_NOTIONAL = "250.00"


def _default_alpaca_client_factory(settings) -> Callable[[str], AlpacaClient]:
    def factory(_: str) -> AlpacaClient:
        return AlpacaClient(
            base_url=settings.alpaca_base_url,
            api_key=settings.alpaca_api_key,
        )

    return factory


@dataclass
class BrokerPrestageService:
    session_factory: sessionmaker[Session]
    settings: object
    alpaca_client_factory: Callable[[str], object] | None = None

    def __post_init__(self) -> None:
        if self.alpaca_client_factory is None:
            self.alpaca_client_factory = _default_alpaca_client_factory(self.settings)

    def prestage_approved_recommendations(
        self,
        run_id: str,
        recommendation_ids: list[int],
        broker_mode: str,
    ) -> list[BrokerArtifact]:
        client = self.alpaca_client_factory(broker_mode)
        if broker_mode not in {"paper", "live"}:
            raise BrokerPolicyError("Unsupported broker mode")

        with self.session_factory.begin() as session:
            recommendations = (
                session.query(RecommendationRecord)
                .filter(
                    RecommendationRecord.run_id == run_id,
                    RecommendationRecord.id.in_(recommendation_ids),
                )
                .order_by(RecommendationRecord.id.asc())
                .all()
            )
            repository = BrokerArtifactsRepository(session)
            artifacts: list[BrokerArtifact] = []

            for recommendation in recommendations:
                recommendation_id = recommendation.id
                client_order_id = f"{run_id}-{recommendation_id}-{broker_mode}"
                proposal = OrderProposal(
                    run_id=run_id,
                    recommendation_id=recommendation_id,
                    broker_mode=BrokerMode(broker_mode),
                    symbol=recommendation.ticker,
                    side=recommendation.action,
                    order_type="market",
                    time_in_force="day",
                    qty=None,
                    notional=DEFAULT_NOTIONAL,
                    client_order_id=client_order_id,
                )
                snapshot = validate_order_proposal(
                    proposal,
                    account=client.get_account(),
                    asset=client.get_asset(recommendation.ticker),
                    broker_mode=broker_mode,
                    base_url=self.settings.alpaca_base_url,
                )
                record = repository.create_artifact(proposal, snapshot)
                artifacts.append(
                    BrokerArtifact(
                        id=record.id,
                        run_id=record.run_id,
                        recommendation_id=record.recommendation_id,
                        broker_mode=BrokerMode(record.broker_mode),
                        symbol=record.symbol,
                        side=record.side,
                        order_type=record.order_type,
                        time_in_force=record.time_in_force,
                        qty=record.qty,
                        notional=record.notional,
                        client_order_id=record.client_order_id,
                        status=record.status,
                        policy_snapshot_json=record.policy_snapshot_json,
                    )
                )

        return artifacts


_default_service: BrokerPrestageService | None = None


def configure_broker_prestage_service(service: BrokerPrestageService) -> None:
    global _default_service
    _default_service = service


def prestage_approved_recommendations(run_id: str, recommendation_ids: list[int], broker_mode: str) -> list[BrokerArtifact]:
    if _default_service is None:
        raise RuntimeError("Broker prestage service is not configured")
    return _default_service.prestage_approved_recommendations(run_id, recommendation_ids, broker_mode)
