from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.runs import RunsRepository
from app.schemas.research import CandidateRecommendation
from app.services.tokens import ApprovalTokenPayload

AWAITING_REVIEW_STATUS = "awaiting_review"
RESUMING_STATUS = "resuming"
COMPLETED_STATUS = "completed"
REJECTED_STATUS = "rejected"
BROKER_PRESTAGED_STATUS = "broker_prestaged"
TERMINAL_STATUSES = {COMPLETED_STATUS, REJECTED_STATUS, BROKER_PRESTAGED_STATUS}


class RunNotAwaitingReviewError(ValueError):
    """Raised when a run is not awaiting review at decision time."""


class DuplicateApprovalError(ValueError):
    """Raised when the same approval token is replayed."""


class StaleApprovalError(ValueError):
    """Raised when a run has already reached a terminal approval outcome."""


class MissingRunError(ValueError):
    """Raised when an approval references a missing run."""


@dataclass
class ApprovalService:
    session_factory: sessionmaker[Session]
    runtime: object
    research_node: object
    prestage_service: Optional[Callable[..., object]] = None
    broker_mode: str = "paper"

    def apply_review_decision(self, payload: ApprovalTokenPayload, token_id: str) -> dict:
        with self.session_factory.begin() as session:
            repository = RunsRepository(session)
            run = repository.get_run(payload.run_id)
            if run is None:
                raise MissingRunError("Run not found")
            if repository.get_approval_event_by_token_id(token_id) is not None:
                raise DuplicateApprovalError("Approval already recorded")
            if run.status in TERMINAL_STATUSES:
                raise StaleApprovalError("Approval already processed")
            if run.status != AWAITING_REVIEW_STATUS:
                raise RunNotAwaitingReviewError("Run is not awaiting review")
            recommendation_rows = repository.list_recommendations(run.run_id)
            recommendation_ids = [row.id for row in recommendation_rows]
            thread_id = run.thread_id

            repository.record_approval_event(
                run_id=run.run_id,
                decision=payload.decision,
                token_id=token_id,
            )

            if payload.decision == "reject":
                repository.transition_run(
                    run,
                    to_status=REJECTED_STATUS,
                    current_step="rejected",
                    approval_status="reject",
                    reason="Approval callback rejected the run",
                )
                return {"run_id": run.run_id, "status": REJECTED_STATUS}

            repository.transition_run(
                run,
                to_status=RESUMING_STATUS,
                current_step="approval",
                approval_status="approve",
                reason="Approval callback accepted the run",
            )
            state_payload = dict(run.state_payload or {})
            state_payload["thread_id"] = thread_id
            state_payload["recommendations"] = [
                item
                if isinstance(item, CandidateRecommendation)
                else CandidateRecommendation.model_validate(item)
                for item in state_payload.get("recommendations", [])
            ]

        result = self.runtime.resume_run(
            state_payload,
            decision=payload.decision,
            research_node=self.research_node,
        )
        final_status = result["status"]
        if self.prestage_service is not None:
            self.prestage_service(
                run_id=payload.run_id,
                recommendation_ids=recommendation_ids,
                broker_mode=self.broker_mode,
            )
            final_status = BROKER_PRESTAGED_STATUS

        with self.session_factory.begin() as session:
            repository = RunsRepository(session)
            run = repository.get_run(payload.run_id)
            if run is None:
                raise MissingRunError("Run not found")
            repository.transition_run(
                run,
                to_status=final_status,
                current_step=final_status,
                approval_status="approve",
                reason="Persisted workflow resumed from approval decision",
            )

        return {
            "run_id": payload.run_id,
            "thread_id": thread_id,
            "status": final_status,
        }


_default_service: ApprovalService | None = None


def configure_approval_service(service: ApprovalService) -> None:
    global _default_service
    _default_service = service


def apply_review_decision(payload: ApprovalTokenPayload, token_id: str) -> dict:
    if _default_service is None:
        raise RuntimeError("Approval service is not configured")
    return _default_service.apply_review_decision(payload, token_id=token_id)
