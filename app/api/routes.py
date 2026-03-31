from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Request

from app.agents.research import ResearchNode
from app.graph.workflow import compile_workflow
from app.services.tokens import verify_approval_token

router = APIRouter()


class StaticLLM:
    def invoke(self, _: dict[str, str]) -> str:
        return (
            '{"recommendations": ['
            '{"ticker": "NVDA", "action": "buy", "conviction_score": 0.81, "rationale": "signal"}'
            "]}"
        )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/runs/trigger", status_code=202)
def trigger_run(request: Request) -> dict[str, str]:
    run_id = f"run-{uuid4().hex[:8]}"
    workflow = compile_workflow(research_node=ResearchNode(llm=StaticLLM()))
    state = workflow.invoke({"run_id": run_id})
    request.app.state.workflow_store[run_id] = {"workflow": workflow, "state": state}
    return {"status": "started", "run_id": run_id}


@router.get("/approval/{token}")
def review_token(token: str, request: Request) -> dict:
    payload = verify_approval_token(
        token,
        secret=request.app.state.settings.app_secret,
        ttl_seconds=900,
    )
    stored = request.app.state.workflow_store[payload.run_id]
    result = stored["workflow"].resume(stored["state"], decision=payload.decision)
    request.app.state.workflow_store[payload.run_id]["state"] = result
    return result
