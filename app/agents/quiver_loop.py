from __future__ import annotations

import json
from typing import Callable, Dict, List, Protocol

from pydantic import TypeAdapter

from app.schemas.quiver import TickerEvidenceBundle
from app.schemas.research import NoActionOutcome, ResearchOutcome
from app.schemas.research_agent import AgentTraceStep, ResearchAgentBudget, ResearchExecutionResult
from app.services.research_prompt import (
    build_final_research_payload,
    build_quiver_loop_system_prompt,
    build_seed_research_brief,
)


class ToolCapableLLM(Protocol):
    def complete_with_tools(
        self,
        *,
        messages: List[Dict[str, object]],
        tools: List[Dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> Dict[str, object]:
        ...


def default_shortlist_selector(
    evidence_bundles: List[TickerEvidenceBundle],
    max_seed_tickers: int,
) -> List[TickerEvidenceBundle]:
    return sorted(
        evidence_bundles,
        key=lambda bundle: (
            -_bundle_priority(bundle),
            -(bundle.latest_signal_at.timestamp() if bundle.latest_signal_at else 0.0),
            len(bundle.contradictory_signals),
            bundle.ticker,
        ),
    )[:max_seed_tickers]


def _bundle_priority(bundle: TickerEvidenceBundle) -> int:
    diversity = len(
        {
            signal.signal_type
            for signal in bundle.supporting_signals + bundle.contradictory_signals
        }
    )
    freshness_bonus = 1 if bundle.latest_signal_at is not None else 0
    net_signal_score = len(bundle.supporting_signals) - len(bundle.contradictory_signals)
    return (freshness_bonus * 100) + (net_signal_score * 10) + diversity


class QuiverLoopAgent:
    def __init__(
        self,
        *,
        llm: ToolCapableLLM,
        budget: ResearchAgentBudget,
        shortlist_selector: Callable[[List[TickerEvidenceBundle], int], List[TickerEvidenceBundle]] = default_shortlist_selector,
    ) -> None:
        self._llm = llm
        self._budget = budget
        self._shortlist_selector = shortlist_selector

    def run(
        self,
        *,
        run_id: str,
        evidence_bundles: List[TickerEvidenceBundle],
        account_context: dict[str, str],
        quiver_client,
    ) -> ResearchExecutionResult:
        shortlisted = self._shortlist_selector(evidence_bundles, self._budget.max_seed_tickers)
        if not shortlisted:
            return self._stop_result(
                stop_reason="empty_ticker_set",
                trace=[],
                tool_call_count=0,
                investigated_tickers=[],
            )

        messages: List[Dict[str, object]] = [
            {
                "role": "system",
                "content": build_quiver_loop_system_prompt(
                    max_steps=self._budget.max_steps,
                    max_tool_calls=self._budget.max_tool_calls,
                ),
            },
            {
                "role": "user",
                "content": build_seed_research_brief(
                    run_id=run_id,
                    evidence_bundles=shortlisted,
                    account_context=account_context,
                    max_seed_tickers=len(shortlisted),
                ),
            },
        ]
        trace: List[AgentTraceStep] = []
        investigated_tickers: List[str] = []
        tool_call_count = 0

        for step_index in range(self._budget.max_steps):
            if tool_call_count >= self._budget.max_tool_calls and trace:
                break

            assistant_message = self._llm.complete_with_tools(
                messages=messages,
                tools=self._tool_definitions(),
                tool_choice="auto",
                parallel_tool_calls=False,
            )
            tool_calls = assistant_message.get("tool_calls") or []
            if tool_calls:
                if tool_call_count >= self._budget.max_tool_calls:
                    break
                tool_call = tool_calls[0]
                function_payload = tool_call["function"]
                tool_name = function_payload["name"]
                tool_args = json.loads(function_payload.get("arguments") or "{}")
                tool_result, tracked_value, tracks_ticker = self._execute_tool(
                    quiver_client,
                    tool_name,
                    tool_args,
                )
                tool_call_count += 1
                if tracks_ticker and tracked_value and tracked_value not in investigated_tickers:
                    investigated_tickers.append(tracked_value)
                trace.append(
                    AgentTraceStep(
                        step_index=step_index,
                        action="tool_call",
                        rationale=str(assistant_message.get("content") or f"Executed {tool_name}."),
                        tool_name=tool_name,
                        tool_args=tool_args,
                        result_summary=f"{len(tool_result)} row(s) returned.",
                    )
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.get("content"),
                        "tool_calls": tool_calls,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps([self._serialize_row(row) for row in tool_result]),
                    }
                )
                continue

            outcome = TypeAdapter(ResearchOutcome).validate_json(assistant_message["content"])
            trace.append(
                AgentTraceStep(
                    step_index=step_index,
                    action="finalize",
                    rationale="Model returned a final research outcome.",
                    result_summary=f"Final outcome: {outcome.outcome}.",
                )
            )
            return ResearchExecutionResult(
                outcome=outcome,
                trace=trace,
                stop_reason="final_answer",
                tool_call_count=tool_call_count,
                investigated_tickers=investigated_tickers,
            )

        return self._stop_result(
            stop_reason="budget_exhausted",
            trace=trace,
            tool_call_count=tool_call_count,
            investigated_tickers=investigated_tickers,
        )

    def _tool_definitions(self) -> List[Dict[str, object]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "parameters": config["parameters"],
                },
            }
            for tool_name, config in self._tool_registry().items()
        ]

    def _tool_registry(self) -> Dict[str, Dict[str, object]]:
        return {
            "get_live_congress_trading": {
                "parameters": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"],
                },
                "arg_name": "ticker",
                "normalize": lambda value: str(value or "").upper(),
                "tracks_ticker": True,
            },
            "get_live_insider_trading": {
                "parameters": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"],
                },
                "arg_name": "ticker",
                "normalize": lambda value: str(value or "").upper(),
                "tracks_ticker": True,
            },
            "get_live_government_contracts": {
                "parameters": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"],
                },
                "arg_name": "ticker",
                "normalize": lambda value: str(value or "").upper(),
                "tracks_ticker": True,
            },
            "get_live_lobbying": {
                "parameters": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"],
                },
                "arg_name": "ticker",
                "normalize": lambda value: str(value or "").upper(),
                "tracks_ticker": True,
            },
            "get_live_bill_summaries": {
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                "arg_name": "query",
                "normalize": lambda value: str(value or ""),
                "tracks_ticker": False,
            },
        }

    def _execute_tool(self, quiver_client, tool_name: str, tool_args: Dict[str, object]):
        config = self._tool_registry()[tool_name]
        arg_name = str(config["arg_name"])
        normalize = config["normalize"]
        value = normalize(tool_args.get(arg_name))
        return getattr(quiver_client, tool_name)(**{arg_name: value}), value, bool(config["tracks_ticker"])

    def _serialize_row(self, row) -> Dict[str, object]:
        if hasattr(row, "model_dump"):
            return row.model_dump(mode="json", by_alias=True)
        return dict(row)

    def _stop_result(
        self,
        *,
        stop_reason: str,
        trace: List[AgentTraceStep],
        tool_call_count: int,
        investigated_tickers: List[str],
    ) -> ResearchExecutionResult:
        outcome = NoActionOutcome(
            outcome="no_action",
            summary="Research loop stopped before a final thesis was reached.",
            reasons=[stop_reason],
        )
        trace_with_stop = list(trace)
        trace_with_stop.append(
            AgentTraceStep(
                step_index=len(trace_with_stop),
                action="stop",
                rationale=f"Loop stopped due to {stop_reason}.",
                result_summary=f"Stop reason: {stop_reason}.",
            )
        )
        return ResearchExecutionResult(
            outcome=outcome,
            trace=trace_with_stop,
            stop_reason=stop_reason,
            tool_call_count=tool_call_count,
            investigated_tickers=investigated_tickers,
        )
