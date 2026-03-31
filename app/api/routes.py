from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.db.models import RunRecord
from app.services.scheduling import create_or_get_scheduled_run
from app.services.run_service import DuplicateApproval, RunNotFound, StaleApproval
from app.services.tokens import verify_approval_token
from app.services.tokens import ExpiredApprovalTokenError, InvalidApprovalTokenError
from app.tools.quiver import QuiverClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    run_id = f"run-{uuid4().hex[:8]}"
    thread_id = f"thread-{uuid4().hex[:12]}"
    quiver_client = QuiverClient(
        base_url=request.app.state.settings.quiver_base_url,
        api_key=request.app.state.settings.quiver_api_key,
        transport=request.app.state.quiver_transport,
    )
    request.app.state.run_service.create_pending_run(
        run_id=run_id,
        thread_id=thread_id,
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )
    state = request.app.state.runtime.start_run(
        run_id=run_id,
        thread_id=thread_id,
        research_node=request.app.state.research_node,
        quiver_client=quiver_client,
        base_url=str(request.base_url).rstrip("/"),
    )
    request.app.state.run_service.store_state_payload(run_id, state)
    request.app.state.run_service.store_recommendations(
        run_id,
        list(state.get("recommendations", [])),
    )
    request.app.state.run_service.mark_status(
        run_id,
        to_status=state["status"],
        current_step="approval",
        reason="Research completed and awaiting operator review",
    )
    return {"status": "started", "run_id": run_id}


@router.post("/runs/trigger/scheduled")
def trigger_scheduled_run(
    request: Request,
    response: Response,
    scheduled_trigger: Optional[str] = Header(default=None, alias="X-Investor-Scheduled-Trigger"),
) -> dict[str, object]:
    if scheduled_trigger != request.app.state.settings.scheduled_trigger_token:
        raise HTTPException(status_code=401, detail="Invalid scheduled trigger token")

    with request.app.state.session_factory() as session:
        run, duplicate = create_or_get_scheduled_run(
            session,
            run_factory=lambda schedule_key: RunRecord(
                run_id=f"run-{uuid4().hex[:8]}",
                thread_id=f"thread-{uuid4().hex[:12]}",
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

    quiver_client = QuiverClient(
        base_url=request.app.state.settings.quiver_base_url,
        api_key=request.app.state.settings.quiver_api_key,
        transport=request.app.state.quiver_transport,
    )
    state = request.app.state.runtime.start_run(
        run_id=run.run_id,
        thread_id=run.thread_id,
        research_node=request.app.state.research_node,
        quiver_client=quiver_client,
        base_url=str(request.base_url).rstrip("/"),
    )
    request.app.state.run_service.store_state_payload(run.run_id, state)
    request.app.state.run_service.store_recommendations(
        run.run_id,
        list(state.get("recommendations", [])),
    )
    request.app.state.run_service.mark_status(
        run.run_id,
        to_status=state["status"],
        current_step="approval",
        reason="Research completed and awaiting operator review",
    )
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
    try:
        payload = verify_approval_token(
            token,
            secret=request.app.state.settings.app_secret,
            ttl_seconds=request.app.state.settings.approval_token_ttl_seconds,
        )
        approval_state = request.app.state.run_service.apply_approval_decision(
            payload.run_id,
            decision=payload.decision,
            token_id=payload.token_id,
        )
    except ExpiredApprovalTokenError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except InvalidApprovalTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RunNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (StaleApproval, DuplicateApproval) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    result = request.app.state.runtime.resume_run(
        approval_state,
        decision=payload.decision,
        research_node=request.app.state.research_node,
    )
    if result["status"] != approval_state["status"]:
        request.app.state.run_service.mark_status(
            payload.run_id,
            to_status=result["status"],
            current_step="completed" if result["status"] == "completed" else "rejected",
            reason="Approval callback processed",
            approval_status=payload.decision,
        )
    return {"status": result["status"], "run_id": payload.run_id}
