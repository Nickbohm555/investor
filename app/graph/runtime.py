from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.graph.workflow import compile_workflow


@dataclass
class InvestorRuntime:
    settings: object
    mail_provider: object = None
    workflow_factory: Callable = compile_workflow

    def start_run(
        self,
        *,
        run_id: str,
        research_node,
        quiver_client,
        workflow=None,
    ) -> dict:
        workflow = workflow or self.workflow_factory(
            research_node,
            self.settings,
            self.mail_provider,
        )
        return workflow.invoke(
            {
                "run_id": run_id,
                "quiver_client": quiver_client,
            }
        )

    def resume_run(self, state: dict, *, decision: str, research_node) -> dict:
        workflow = self.workflow_factory(
            research_node,
            self.settings,
            self.mail_provider,
        )
        return workflow.resume(state, decision=decision)
