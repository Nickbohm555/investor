from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ApprovalEventRecord, RecommendationRecord, RunRecord
from app.repositories.run_repository import RunRepository
from app.schemas.research import CandidateRecommendation
from app.schemas.workflow import Recommendation

TRIGGERED_STATUS = "triggered"
AWAITING_HUMAN_REVIEW_STATUS = "awaiting_human_review"
APPROVED_STATUS = "approved"
COMPLETED_STATUS = "completed"
REJECTED_STATUS = "rejected"


class RunNotFound(ValueError):
    pass


class StaleApproval(ValueError):
    pass


class DuplicateApproval(ValueError):
    pass


class RunService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_pending_run(
        self,
        *,
        run_id: str,
        status: str,
        current_step: str,
        trigger_source: str,
        approval_status: str = "pending",
    ) -> RunRecord:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            run = repository.create_run(
                run_id=run_id,
                status=status,
                current_step=current_step,
                trigger_source=trigger_source,
                approval_status=approval_status,
            )
        return run

    def store_recommendations(
        self, run_id: str, recommendations: list
    ) -> list[RecommendationRecord]:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            normalized = [
                _normalize_recommendation_input(item)
                for item in recommendations
            ]
            rows = repository.replace_recommendations(run_id, normalized)
        return rows

    def store_state_payload(self, run_id: str, state: dict) -> RunRecord:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            run = repository.update_state_payload(run_id, _serialize_state(state))
        return run

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

    def apply_approval_decision(
        self, run_id: str, *, decision: str, token_id: str
    ) -> dict:
        with self.session_factory.begin() as session:
            repository = RunRepository(session)
            run = repository.get_run(run_id)
            if run is None:
                raise RunNotFound("Run not found")
            if session.query(ApprovalEventRecord).filter_by(token_id=token_id).first() is not None:
                raise DuplicateApproval("Approval already recorded")
            if run.status in {COMPLETED_STATUS, REJECTED_STATUS}:
                raise StaleApproval("Approval already processed")

            repository.record_approval_event(
                run_id=run_id,
                decision=decision,
                token_id=token_id,
            )
            next_status = APPROVED_STATUS if decision == "approve" else REJECTED_STATUS
            repository.record_transition(
                run_id,
                from_status=run.status,
                to_status=next_status,
                reason="Approval callback accepted",
            )
            run.status = next_status
            run.approval_status = decision
            run.current_step = "approval"
            recommendations = [
                Recommendation(
                    ticker=row.ticker,
                    action=row.action,
                    conviction_score=0.81,
                    rationale=row.rationale,
                )
                for row in repository.list_recommendations(run_id)
            ]
            session.flush()
            return {
                "run_id": run.run_id,
                "status": run.status,
                "current_step": run.current_step,
                "recommendations": recommendations,
            }

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self.session_factory() as session:
            repository = RunRepository(session)
            return repository.get_run(run_id)

    def get_latest_report_baseline(self, *, exclude_run_id: str) -> dict | None:
        return None

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


def _recommendation_rationale(item) -> str:
    if isinstance(item, CandidateRecommendation):
        for values in (item.source_summary, item.supporting_evidence, item.risk_notes):
            if values:
                return "; ".join(values)
        return item.action
    return getattr(item, "rationale", getattr(item, "action", ""))


def _normalize_recommendation_input(item) -> Recommendation:
    if isinstance(item, Recommendation):
        return item
    if isinstance(item, CandidateRecommendation):
        return Recommendation(
            ticker=item.ticker,
            action=item.action,
            conviction_score=item.conviction_score,
            rationale=_recommendation_rationale(item),
        )
    if isinstance(item, dict):
        if "rationale" in item:
            return Recommendation.model_validate(item)
        candidate = CandidateRecommendation.model_validate(item)
        return Recommendation(
            ticker=candidate.ticker,
            action=candidate.action,
            conviction_score=candidate.conviction_score,
            rationale=_recommendation_rationale(candidate),
        )
    return Recommendation(
        ticker=item.ticker,
        action=item.action,
        conviction_score=item.conviction_score,
        rationale=_recommendation_rationale(item),
    )


def _serialize_state(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return {key: _serialize_state(item) for key, item in value.model_dump(mode="python").items()}
    if isinstance(value, dict):
        return {key: _serialize_state(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_state(item) for item in value]
    return value
