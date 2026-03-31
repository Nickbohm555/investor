from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.runs import RunsRepository
from app.services.tokens import ApprovalTokenPayload

AWAITING_REVIEW_STATUS = "awaiting_review"
COMPLETED_STATUS = "completed"
REJECTED_STATUS = "rejected"
BROKER_PRESTAGED_STATUS = "broker_prestaged"
ARCHIVED_PRE_PHASE6_STATUS = "archived_pre_phase6"
ARCHIVED_PRE_PHASE6_DETAIL = "Run was archived during the Phase 6 cutover and can no longer be approved"
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
    workflow_engine: object
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
            if (
                run.status == ARCHIVED_PRE_PHASE6_STATUS
                or run.current_step == ARCHIVED_PRE_PHASE6_STATUS
            ):
                raise StaleApprovalError(ARCHIVED_PRE_PHASE6_DETAIL)
            if run.status in TERMINAL_STATUSES:
                raise StaleApprovalError("Approval already processed")
            if run.status != AWAITING_REVIEW_STATUS:
                raise RunNotAwaitingReviewError("Run is not awaiting review")
            recommendation_rows = repository.list_recommendations(run.run_id)
            recommendation_ids = [row.id for row in recommendation_rows]

            repository.record_approval_event(
                run_id=run.run_id,
                decision=payload.decision,
                token_id=token_id,
            )

        result = self.workflow_engine.advance_run(
            run_id=payload.run_id,
            event=f"approval:{payload.decision}",
        )
        if payload.decision == "approve" and self.prestage_service is not None:
            _handoff = result.get("handoff")
            self.prestage_service(
                run_id=payload.run_id,
                recommendation_ids=recommendation_ids,
                broker_mode=self.broker_mode,
            )

        return {
            "run_id": payload.run_id,
            "status": result["status"],
        }


_default_service: ApprovalService | None = None


def configure_approval_service(service: ApprovalService) -> None:
    global _default_service
    _default_service = service


def apply_review_decision(payload: ApprovalTokenPayload, token_id: str) -> dict:
    if _default_service is None:
        raise RuntimeError("Approval service is not configured")
    return _default_service.apply_review_decision(payload, token_id=token_id)
