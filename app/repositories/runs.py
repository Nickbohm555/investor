from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord, StateTransitionRecord


class RunsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        return self.session.get(RunRecord, run_id)

    def get_approval_event_by_token_id(self, token_id: str) -> Optional[ApprovalEventRecord]:
        return self.session.query(ApprovalEventRecord).filter_by(token_id=token_id).first()

    def list_recommendations(self, run_id: str) -> list[RecommendationRecord]:
        return (
            self.session.query(RecommendationRecord)
            .filter_by(run_id=run_id)
            .order_by(RecommendationRecord.id.asc())
            .all()
        )

    def update_state_payload(self, run: RunRecord, state_payload: dict | None) -> RunRecord:
        run.state_payload = state_payload
        self.session.flush()
        return run

    def record_approval_event(self, *, run_id: str, decision: str, token_id: str) -> ApprovalEventRecord:
        event = ApprovalEventRecord(
            run_id=run_id,
            decision=decision,
            token_id=token_id,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def transition_run(
        self,
        run: RunRecord,
        *,
        to_status: str,
        current_step: str,
        approval_status: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> RunRecord:
        transition = StateTransitionRecord(
            run_id=run.run_id,
            from_status=run.status,
            to_status=to_status,
            reason=reason,
        )
        self.session.add(transition)
        run.status = to_status
        run.current_step = current_step
        if approval_status is not None:
            run.approval_status = approval_status
        self.session.flush()
        return run
