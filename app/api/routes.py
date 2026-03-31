from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.db.models import RunRecord
from app.graph.workflow import compile_workflow
from app.services.approvals import (
    ApprovalService,
    DuplicateApprovalError,
    MissingRunError,
    RunNotAwaitingReviewError,
    StaleApprovalError,
    apply_review_decision,
    configure_approval_service,
)
from app.services.scheduling import create_or_get_scheduled_run
from app.services.tokens import ExpiredApprovalTokenError, InvalidApprovalTokenError
from app.services.tokens import verify_approval_token
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
    workflow = compile_workflow(
        request.app.state.research_node,
        request.app.state.settings,
        request.app.state.mail_provider,
    )
    state = request.app.state.runtime.start_run(
        run_id=run_id,
        thread_id=thread_id,
        research_node=request.app.state.research_node,
        quiver_client=quiver_client,
        workflow=workflow,
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
    workflow = compile_workflow(
        request.app.state.research_node,
        request.app.state.settings,
        request.app.state.mail_provider,
    )
    try:
        state = request.app.state.runtime.start_run(
            run_id=run.run_id,
            thread_id=run.thread_id,
            research_node=request.app.state.research_node,
            quiver_client=quiver_client,
            workflow=workflow,
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
    try:
        payload = verify_approval_token(
            token,
            secret=request.app.state.settings.app_secret,
            ttl_seconds=request.app.state.settings.approval_token_ttl_seconds,
        )
        configure_approval_service(
            ApprovalService(
                session_factory=request.app.state.session_factory,
                runtime=request.app.state.runtime,
                research_node=request.app.state.research_node,
            )
        )
        result = apply_review_decision(payload, token_id=payload.token_id)
    except ExpiredApprovalTokenError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except InvalidApprovalTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MissingRunError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StaleApprovalError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except (DuplicateApprovalError, RunNotAwaitingReviewError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": result["status"], "run_id": payload.run_id}
