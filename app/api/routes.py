from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Request

from app.schemas.workflow import Recommendation
from app.services.tokens import verify_approval_token

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
    payload = verify_approval_token(
        token,
        secret=request.app.state.settings.app_secret,
        ttl_seconds=request.app.state.settings.approval_token_ttl_seconds,
    )
    run = request.app.state.run_service.get_run(payload.run_id)
    recommendations = request.app.state.run_service.list_recommendations(payload.run_id)
    result = request.app.state.runtime.resume_run(
        {
            "run_id": payload.run_id,
            "thread_id": run.thread_id,
            "status": run.status,
            "recommendations": [
                item if isinstance(item, Recommendation) else Recommendation.model_validate(item)
                for item in recommendations
            ],
        },
        decision=payload.decision,
        research_node=request.app.state.research_node,
    )
    request.app.state.run_service.mark_status(
        payload.run_id,
        to_status=result["status"],
        current_step="completed" if result["status"] == "completed" else "rejected",
        reason="Approval callback processed",
        approval_status=payload.decision,
    )
    return result
