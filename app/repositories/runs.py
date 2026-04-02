from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord, StateTransitionRecord
from app.schemas.workflow import Recommendation


class RunsRepository:
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

    def get_latest_delivered_report_run(self, *, exclude_run_id: str) -> RunRecord | None:
        candidates = (
            self.session.query(RunRecord)
            .filter(
                RunRecord.run_id != exclude_run_id,
                RunRecord.status == "completed",
                RunRecord.state_payload.isnot(None),
            )
            .order_by(RunRecord.created_at.desc())
            .all()
        )
        for run in candidates:
            payload = run.state_payload or {}
            if payload.get("email_body") is not None:
                return run
        return None

    def get_approval_event_by_token_id(self, token_id: str) -> Optional[ApprovalEventRecord]:
        return self.session.query(ApprovalEventRecord).filter_by(token_id=token_id).first()

    def list_recommendations(self, run_id: str) -> list[RecommendationRecord]:
        return (
            self.session.query(RecommendationRecord)
            .filter_by(run_id=run_id)
            .order_by(RecommendationRecord.id.asc())
            .all()
        )

    def replace_recommendations(
        self,
        run_id: str,
        recommendations: list[Recommendation],
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
