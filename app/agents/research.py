from __future__ import annotations

from typing import Callable, List, Optional, Protocol

from pydantic import TypeAdapter

from app.agents.quiver_loop import QuiverLoopAgent
from app.schemas.quiver import TickerEvidenceBundle
from app.schemas.research import ResearchOutcome
from app.schemas.research_agent import AgentTraceStep, ResearchAgentBudget, ResearchExecutionResult
from app.services.research_prompt import build_research_prompt_payload


class InvokableLLM(Protocol):
    def invoke(self, payload: dict[str, str]) -> str:
        ...


class ToolCapableLLM(InvokableLLM, Protocol):
    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        ...


class ResearchNode:
    def __init__(
        self,
        llm: InvokableLLM,
        prompt_builder: Callable[[str, List[TickerEvidenceBundle], dict[str, str]], dict[str, str]] = build_research_prompt_payload,
        budget: Optional[ResearchAgentBudget] = None,
    ) -> None:
        self._agent = llm
        self._prompt_builder = prompt_builder
        self._budget = budget or ResearchAgentBudget(
            max_steps=4,
            max_tool_calls=3,
            max_seed_tickers=3,
        )

    def run(
        self,
        run_id: str,
        evidence_bundles: List[TickerEvidenceBundle],
        account_context: dict[str, str],
        quiver_client=None,
    ) -> ResearchOutcome:
        return self.run_with_trace(
            run_id=run_id,
            evidence_bundles=evidence_bundles,
            account_context=account_context,
            quiver_client=quiver_client,
        ).outcome

    def run_with_trace(
        self,
        run_id: str,
        evidence_bundles: List[TickerEvidenceBundle],
        account_context: dict[str, str],
        quiver_client,
    ) -> ResearchExecutionResult:
        if hasattr(self._agent, "complete_with_tools") and quiver_client is not None:
            return QuiverLoopAgent(
                llm=self._agent,  # type: ignore[arg-type]
                budget=self._budget,
            ).run(
                run_id=run_id,
                evidence_bundles=evidence_bundles,
                account_context=account_context,
                quiver_client=quiver_client,
            )

        payload = self._prompt_builder(run_id, evidence_bundles, account_context)
        response = self._agent.invoke(payload)
        outcome = TypeAdapter(ResearchOutcome).validate_json(response)
        return ResearchExecutionResult(
            outcome=outcome,
            trace=[
                AgentTraceStep(
                    step_index=0,
                    action="finalize",
                    rationale="Completed with the legacy JSON-only research path.",
                    result_summary=f"Final outcome: {outcome.outcome}.",
                )
            ],
            stop_reason="final_answer",
            tool_call_count=0,
            investigated_tickers=[],
        )
