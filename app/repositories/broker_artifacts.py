from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import BrokerArtifactRecord
from app.schemas.broker import BrokerPolicySnapshot, OrderProposal


def create_artifact(proposal: OrderProposal, snapshot: BrokerPolicySnapshot) -> BrokerArtifactRecord:
    return BrokerArtifactRecord(
        run_id=proposal.run_id,
        recommendation_id=proposal.recommendation_id,
        broker_mode=proposal.broker_mode.value,
        symbol=proposal.symbol,
        side=proposal.side,
        order_type=proposal.order_type,
        time_in_force=proposal.time_in_force,
        qty=proposal.qty,
        notional=proposal.notional,
        client_order_id=proposal.client_order_id,
        status="draft_ready",
        policy_snapshot_json=snapshot.model_dump(mode="json"),
    )


class BrokerArtifactsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_artifact(self, proposal: OrderProposal, snapshot: BrokerPolicySnapshot) -> BrokerArtifactRecord:
        artifact = create_artifact(proposal, snapshot)
        self.session.add(artifact)
        self.session.flush()
        return artifact
