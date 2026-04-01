from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import RecommendationRecord, RunRecord
from app.repositories.runs import RunsRepository
from app.schemas.research import CandidateRecommendation
from app.schemas.workflow import Recommendation

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
            return RunsRepository(session).create_run(
                run_id=run_id,
                status=status,
                current_step=current_step,
                trigger_source=trigger_source,
                approval_status=approval_status,
            )

    def store_recommendations(
        self, run_id: str, recommendations: list
    ) -> list[RecommendationRecord]:
        with self.session_factory.begin() as session:
            normalized = [_normalize_recommendation_input(item) for item in recommendations]
            return RunsRepository(session).replace_recommendations(run_id, normalized)

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self.session_factory() as session:
            return RunsRepository(session).get_run(run_id)

    def get_latest_report_baseline(self, *, exclude_run_id: str) -> dict | None:
        with self.session_factory() as session:
            run = RunsRepository(session).get_latest_delivered_report_run(
                exclude_run_id=exclude_run_id
            )
            if run is None:
                return None
            payload = run.state_payload or {}
            if payload.get("finalized_outcome") is None or payload.get("strategic_report") is None:
                return None
            return {
                "run_id": run.run_id,
                "finalized_outcome": payload["finalized_outcome"],
                "strategic_report": payload["strategic_report"],
            }


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
