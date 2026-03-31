from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.services.run_service import DuplicateApproval, RunNotFound, StaleApproval
from app.services.tokens import verify_approval_token
from app.services.tokens import ExpiredApprovalTokenError, InvalidApprovalTokenError

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    run_id = f"run-{uuid4().hex[:8]}"
    thread_id = f"thread-{uuid4().hex[:12]}"
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
        base_url=str(request.base_url).rstrip("/"),
    )
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
