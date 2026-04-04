from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.db.models import RunRecord
from app.services.approvals import (
    DuplicateApprovalError,
    MissingRunError,
    RunNotAwaitingReviewError,
    StaleApprovalError,
)
from app.services.broker_policy import BrokerPolicyError
from app.services.scheduling import create_or_get_scheduled_run
from app.services.tokens import ExpiredApprovalTokenError, InvalidApprovalTokenError
from app.services.tokens import verify_approval_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    runtime = request.app.state.runtime
    run_id = f"run-{uuid4().hex[:8]}"
    runtime.run_service.create_pending_run(
        run_id=run_id,
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )
    baseline_report = runtime.run_service.get_latest_report_baseline(
        exclude_run_id=run_id,
    )
    try:
        state = runtime.workflow_engine.start_run(
            run_id=run_id,
            quiver_client=runtime.create_quiver_client(),
            baseline_report=baseline_report,
        )
        runtime.run_service.store_recommendations(
            run_id,
            list(state["state_payload"].get("recommendations", [])),
        )
    except Exception as exc:
        logger.exception("manual_trigger result=failure run_id=%s", run_id)
        raise HTTPException(
            status_code=500,
            detail={"message": "Manual trigger failed", "run_id": run_id},
        ) from exc
    logger.info("manual_trigger result=started run_id=%s", run_id)
    return {"status": "started", "run_id": run_id}


@router.post("/runs/trigger/scheduled")
def trigger_scheduled_run(
    request: Request,
    response: Response,
    scheduled_trigger: Optional[str] = Header(default=None, alias="X-Investor-Scheduled-Trigger"),
) -> dict[str, object]:
    runtime = request.app.state.runtime
    if scheduled_trigger != runtime.settings.scheduled_trigger_token:
        raise HTTPException(status_code=401, detail="Invalid scheduled trigger token")

    with runtime.session_factory() as session:
        run, duplicate = create_or_get_scheduled_run(
            session,
            run_factory=lambda schedule_key: RunRecord(
                run_id=f"run-{uuid4().hex[:8]}",
                status="triggered",
                current_step="research",
                trigger_source="scheduled",
                schedule_key=schedule_key,
                replay_of_run_id=None,
            ),
        )

    if duplicate:
        response.status_code = 200
        logger.info(
            "scheduled_trigger result=duplicate schedule_key=%s run_id=%s",
            run.schedule_key,
            run.run_id,
        )
        return {
            "status": "duplicate",
            "run_id": run.run_id,
            "schedule_key": run.schedule_key or "",
            "duplicate": True,
        }

    try:
        baseline_report = runtime.run_service.get_latest_report_baseline(
            exclude_run_id=run.run_id,
        )
        state = runtime.workflow_engine.start_run(
            run_id=run.run_id,
            quiver_client=runtime.create_quiver_client(),
            baseline_report=baseline_report,
        )
        runtime.run_service.store_recommendations(
            run.run_id,
            list(state["state_payload"].get("recommendations", [])),
        )
    except Exception as exc:
        logger.exception(
            "scheduled_trigger result=failure schedule_key=%s run_id=%s",
            run.schedule_key,
            run.run_id,
        )
        raise HTTPException(status_code=500, detail="Scheduled trigger failed") from exc
    response.status_code = 202
    logger.info(
        "scheduled_trigger result=started schedule_key=%s run_id=%s",
        run.schedule_key,
        run.run_id,
    )
    return {
        "status": "started",
        "run_id": run.run_id,
        "schedule_key": run.schedule_key or "",
        "duplicate": False,
    }


@router.get("/approval/{token}")
def review_token(token: str, request: Request) -> dict:
    runtime = request.app.state.runtime
    try:
        payload = verify_approval_token(
            token,
            secret=runtime.settings.app_secret,
            ttl_seconds=runtime.settings.approval_token_ttl_seconds,
        )
        result = runtime.approval_service.apply_review_decision(payload, token_id=payload.token_id)
    except ExpiredApprovalTokenError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except InvalidApprovalTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MissingRunError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StaleApprovalError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except BrokerPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (DuplicateApprovalError, RunNotAwaitingReviewError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": result["status"], "run_id": payload.run_id}


@router.post("/runs/{run_id}/execute")
def execute_run(
    run_id: str,
    request: Request,
    execution_trigger: Optional[str] = Header(default=None, alias="X-Investor-Execution-Trigger"),
) -> dict[str, object]:
    runtime = request.app.state.runtime
    if execution_trigger != runtime.settings.execution_trigger_token:
        raise HTTPException(status_code=401, detail="Invalid execution trigger token")

    try:
        result = runtime.workflow_engine.advance_run(
            run_id=run_id,
            event="execution:confirm",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "status": result["status"],
        "run_id": run_id,
        "submitted_order_count": result["submitted_order_count"],
    }
