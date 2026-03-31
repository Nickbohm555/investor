from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.graph.workflow import compile_workflow


class NoopCheckpointer:
    def setup(self) -> None:
        return None


def _default_checkpointer_factory(connection_string: str):
    if not connection_string.startswith("postgresql"):
        return NoopCheckpointer()
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError:
        return NoopCheckpointer()

    if hasattr(PostgresSaver, "from_conn_string"):
        return PostgresSaver.from_conn_string(connection_string)
    return PostgresSaver(connection_string)


@dataclass
class InvestorRuntime:
    settings: object
    mail_provider: object = None
    workflow_factory: Callable = compile_workflow
    checkpointer_factory: Callable[[str], object] = _default_checkpointer_factory

    def __post_init__(self) -> None:
        self._checkpointer = None
        self._checkpointer_context = None
        self._bootstrapped = False

    def start_run(
        self,
        *,
        run_id: str,
        thread_id: str,
        research_node,
        quiver_client,
        workflow=None,
    ) -> dict:
        workflow = workflow or self._compile_workflow(research_node)
        return workflow.invoke(
            {
                "run_id": run_id,
                "thread_id": thread_id,
                "quiver_client": quiver_client,
            }
        )

    def resume_run(self, state: dict, *, decision: str, research_node) -> dict:
        workflow = self._compile_workflow(research_node)
        return workflow.resume(state, decision=decision)

    def _compile_workflow(self, research_node):
        self._ensure_checkpointer()
        return self.workflow_factory(research_node, self.settings, self.mail_provider, self._checkpointer)

    def _ensure_checkpointer(self) -> None:
        if self._checkpointer is None:
            connection_string = (
                getattr(self.settings, "langgraph_checkpointer_url", None)
                or self.settings.database_url
            )
            checkpointer = self.checkpointer_factory(connection_string)
            if hasattr(checkpointer, "__enter__") and not hasattr(checkpointer, "setup"):
                self._checkpointer_context = checkpointer
                checkpointer = checkpointer.__enter__()
            self._checkpointer = checkpointer
        if not self._bootstrapped:
            self._checkpointer.setup()
            self._bootstrapped = True
