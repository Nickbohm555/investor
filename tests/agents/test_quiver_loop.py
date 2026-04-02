from __future__ import annotations

import json

from app.agents.quiver_loop import QuiverLoopAgent
from app.schemas.quiver import TickerEvidenceBundle
from app.schemas.research_agent import ResearchAgentBudget


class _ToolCapableLLMStub:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls,
            }
        )
        return self._responses.pop(0)


class _QuiverClientStub:
    def __init__(self) -> None:
        self.bill_summary_queries: list[str] = []

    def get_live_bill_summaries(self, query: str | None = None):
        self.bill_summary_queries.append(query or "")
        return [
            {
                "Title": "Energy Permitting Reform",
                "Summary": "Creates faster permitting for grid projects.",
                "Number": "S.42",
            }
        ]


def _bundle() -> TickerEvidenceBundle:
    return TickerEvidenceBundle(
        ticker="NVDA",
        supporting_signals=[],
        contradictory_signals=[],
        source_summary=["Initial evidence bundle."],
    )


def test_quiver_loop_executes_bill_summary_queries_without_forcing_ticker_uppercase() -> None:
    llm = _ToolCapableLLMStub(
        responses=[
            {
                "content": "Check current energy legislation before deciding whether the thesis has policy support.",
                "tool_calls": [
                    {
                        "id": "tool-1",
                        "function": {
                            "name": "get_live_bill_summaries",
                            "arguments": json.dumps({"query": "energy tax credits"}),
                        },
                    }
                ],
            },
            {
                "content": json.dumps(
                    {
                        "outcome": "no_action",
                        "summary": "Policy backdrop is still too uncertain.",
                        "reasons": ["Need clearer legislative follow-through."],
                    }
                )
            },
        ]
    )
    client = _QuiverClientStub()

    result = QuiverLoopAgent(
        llm=llm,
        budget=ResearchAgentBudget(max_steps=3, max_tool_calls=1, max_seed_tickers=1),
    ).run(
        run_id="run-16",
        evidence_bundles=[_bundle()],
        account_context={"account_size": "paper"},
        quiver_client=client,
    )

    assert client.bill_summary_queries == ["energy tax credits"]
    assert result.tool_call_count == 1
    assert result.investigated_tickers == []


def test_quiver_loop_persists_model_rationale_for_follow_up_tool_calls() -> None:
    llm = _ToolCapableLLMStub(
        responses=[
            {
                "content": "Conflicting signals remain, so inspect legislation that could validate the thesis before finalizing.",
                "tool_calls": [
                    {
                        "id": "tool-1",
                        "function": {
                            "name": "get_live_bill_summaries",
                            "arguments": json.dumps({"query": "semiconductor manufacturing"}),
                        },
                    }
                ],
            },
            {
                "content": json.dumps(
                    {
                        "outcome": "no_action",
                        "summary": "Evidence is still incomplete.",
                        "reasons": ["No decisive confirmation yet."],
                    }
                )
            },
        ]
    )

    result = QuiverLoopAgent(
        llm=llm,
        budget=ResearchAgentBudget(max_steps=3, max_tool_calls=1, max_seed_tickers=1),
    ).run(
        run_id="run-16",
        evidence_bundles=[_bundle()],
        account_context={"account_size": "paper"},
        quiver_client=_QuiverClientStub(),
    )

    assert result.trace[0].action == "tool_call"
    assert result.trace[0].rationale == (
        "Conflicting signals remain, so inspect legislation that could validate the thesis before finalizing."
    )
    assert result.trace[0].tool_name == "get_live_bill_summaries"
