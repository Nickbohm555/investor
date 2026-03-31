from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import (
    ApprovalEventRecord,
    RecommendationRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.schemas.workflow import Recommendation


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        run_id: str,
        status: str,
        current_step: str,
        trigger_source: str,
        approval_status: str = "pending",
    ) -> RunRecord:
        run = RunRecord(
            run_id=run_id,
            status=status,
            trigger_source=trigger_source,
            approval_status=approval_status,
            current_step=current_step,
            state_payload=None,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        return self.session.get(RunRecord, run_id)

    def list_recommendations(self, run_id: str) -> list[RecommendationRecord]:
        return (
            self.session.query(RecommendationRecord)
            .filter_by(run_id=run_id)
            .order_by(RecommendationRecord.id.asc())
            .all()
        )

    def replace_recommendations(
        self, run_id: str, recommendations: list[Recommendation]
    ) -> list[RecommendationRecord]:
        self.session.query(RecommendationRecord).filter_by(run_id=run_id).delete()
        rows = [
            RecommendationRecord(
                run_id=run_id,
                ticker=recommendation.ticker,
                action=recommendation.action,
                rationale=recommendation.rationale,
            )
            for recommendation in recommendations
        ]
        self.session.add_all(rows)
        self.session.flush()
        return rows

    def update_state_payload(self, run_id: str, state_payload: dict) -> RunRecord:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        run.state_payload = state_payload
        self.session.flush()
        return run

    def record_transition(
        self,
        run_id: str,
        from_status: str,
        to_status: str,
        reason: Optional[str] = None,
    ) -> StateTransitionRecord:
        transition = StateTransitionRecord(
            run_id=run_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )
        self.session.add(transition)
        self.session.flush()
        return transition

    def record_approval_event(
        self, run_id: str, decision: str, token_id: str
    ) -> ApprovalEventRecord:
        event = ApprovalEventRecord(
            run_id=run_id,
            decision=decision,
            token_id=token_id,
        )
        self.session.add(event)
        self.session.flush()
        return event
