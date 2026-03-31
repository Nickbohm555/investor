from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord
from app.repositories.run_repository import RunRepository
from app.schemas.workflow import Recommendation

TRIGGERED_STATUS = "triggered"
AWAITING_HUMAN_REVIEW_STATUS = "awaiting_human_review"
APPROVED_STATUS = "approved"
COMPLETED_STATUS = "completed"


class RunService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_pending_run(
        self,
        *,
        run_id: str,
        thread_id: str,
        status: str,
        current_step: str,
        trigger_source: str,
        approval_status: str = "pending",
    ) -> RunRecord:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            run = repository.create_run(
                run_id=run_id,
                thread_id=thread_id,
                status=status,
                current_step=current_step,
                trigger_source=trigger_source,
                approval_status=approval_status,
            )
        return run

    def store_recommendations(
        self, run_id: str, recommendations: list[Recommendation]
    ) -> list[RecommendationRecord]:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            rows = repository.replace_recommendations(run_id, recommendations)
        return rows

    def mark_status(
        self,
        run_id: str,
        *,
        to_status: str,
        current_step: str,
        reason: Optional[str] = None,
        approval_status: Optional[str] = None,
    ) -> RunRecord:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            run = repository.get_run(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            from_status = run.status
            run.status = to_status
            run.current_step = current_step
            if approval_status is not None:
                run.approval_status = approval_status
            repository.record_transition(
                run_id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
            )
            session.flush()
        return run

    def record_approval_event(
        self, run_id: str, *, decision: str, token_id: str
    ) -> ApprovalEventRecord:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            event = repository.record_approval_event(
                run_id=run_id,
                decision=decision,
                token_id=token_id,
            )
        return event

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self.session_factory() as session:
            repository = RunRepository(session)
            return repository.get_run(run_id)

    def list_recommendations(self, run_id: str) -> list[Recommendation]:
        with self.session_factory() as session:
            repository = RunRepository(session)
            rows = repository.list_recommendations(run_id)
            return [
                Recommendation(
                    ticker=row.ticker,
                    action=row.action,
                    conviction_score=0.81,
                    rationale=row.rationale,
                )
                for row in rows
            ]
