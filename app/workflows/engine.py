from __future__ import annotations

from typing import Callable

from app.graph.workflow import compile_workflow
from app.workflows.state import WorkflowEvent, WorkflowResult


class WorkflowEngine:
    def __init__(
        self,
        *,
        research_node: object,
        settings: object,
        mail_provider: object,
        workflow_factory: Callable[..., object] = compile_workflow,
    ) -> None:
        self._research_node = research_node
        self._settings = settings
        self._mail_provider = mail_provider
        self._workflow_factory = workflow_factory
        self._paused_runs: dict[str, dict] = {}

    def start_run(self, *, run_id: str, quiver_client: object) -> dict:
        workflow = self._compile_workflow()
        result = workflow.invoke(
            {
                "run_id": run_id,
                "quiver_client": quiver_client,
            }
        )
        self._paused_runs[run_id] = dict(result)
        return WorkflowResult(
            status=result["status"],
            current_step=result["current_step"],
            state_payload=result,
        ).to_dict()

    def advance_run(self, *, run_id: str, event: str) -> dict:
        if event not in {"approval:approve", "approval:reject"}:
            raise ValueError(f"Unsupported workflow event: {event}")
        if run_id not in self._paused_runs:
            raise ValueError(f"Run {run_id} is not loaded")

        workflow = self._compile_workflow()
        decision: WorkflowEvent = event  # type: ignore[assignment]
        paused_state = dict(self._paused_runs[run_id])
        result = workflow.resume(paused_state, decision=decision.split(":", 1)[1])
        self._paused_runs[run_id] = dict(result)
        return WorkflowResult(
            status=result["status"],
            current_step=result["current_step"],
            state_payload=result,
            handoff=result.get("handoff"),
        ).to_dict()

    def _compile_workflow(self):
        return self._workflow_factory(
            self._research_node,
            self._settings,
            self._mail_provider,
        )
