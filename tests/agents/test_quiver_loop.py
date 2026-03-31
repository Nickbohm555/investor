from __future__ import annotations

from app.agents.quiver_loop import QuiverLoopAgent
from app.schemas.quiver import CongressionalTrade, InsiderTrade, SignalRecord, TickerEvidenceBundle
from app.schemas.research_agent import ResearchAgentBudget


class FakeToolLLM:
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


class StubQuiverClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def get_live_congress_trading(self, ticker: str | None = None):
        self.calls.append(("get_live_congress_trading", ticker))
        return [CongressionalTrade(Ticker=ticker or "NVDA", Transaction="Purchase")]

    def get_live_insider_trading(self, ticker: str | None = None):
        self.calls.append(("get_live_insider_trading", ticker))
        return [InsiderTrade(Ticker=ticker or "NVDA", Transaction="Buy")]

    def get_live_government_contracts(self, ticker: str | None = None):
        self.calls.append(("get_live_government_contracts", ticker))
        return []

    def get_live_lobbying(self, ticker: str | None = None):
        self.calls.append(("get_live_lobbying", ticker))
        return []


def _bundle(
    ticker: str,
    *,
    supporting_count: int,
    contradictory_count: int = 0,
) -> TickerEvidenceBundle:
    return TickerEvidenceBundle(
        ticker=ticker,
        supporting_signals=[
            SignalRecord(
                signal_type="congress",
                ticker=ticker,
                direction="positive",
                magnitude_note=f"Support {idx}",
                source_note=f"Support {idx}",
            )
            for idx in range(supporting_count)
        ],
        contradictory_signals=[
            SignalRecord(
                signal_type="lobbying",
                ticker=ticker,
                direction="mixed",
                magnitude_note=f"Risk {idx}",
                source_note=f"Risk {idx}",
            )
            for idx in range(contradictory_count)
        ],
        source_summary=[f"{ticker} summary"],
    )


def test_quiver_loop_agent_uses_seed_shortlist_and_only_ticker_scoped_followups():
    llm = FakeToolLLM(
        responses=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "get_live_congress_trading",
                            "arguments": '{"ticker":"NVDA"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.82,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Signals aligned"],"broker_eligible":true}]}',
                "tool_calls": [],
            },
        ]
    )
    quiver_client = StubQuiverClient()
    agent = QuiverLoopAgent(
        llm=llm,
        budget=ResearchAgentBudget(max_steps=3, max_tool_calls=2, max_seed_tickers=2),
    )

    result = agent.run(
        run_id="run-123",
        evidence_bundles=[
            _bundle("NVDA", supporting_count=3),
            _bundle("MSFT", supporting_count=2),
            _bundle("AAPL", supporting_count=0, contradictory_count=2),
        ],
        account_context={"buying_power": "1000"},
        quiver_client=quiver_client,
    )

    assert result.stop_reason == "final_answer"
    assert result.tool_call_count == 1
    assert result.investigated_tickers == ["NVDA"]
    assert result.outcome.outcome == "candidates"
    assert "Ticker: AAPL" not in llm.calls[0]["messages"][1]["content"]
    assert all(ticker is not None for _, ticker in quiver_client.calls)
    assert quiver_client.calls == [("get_live_congress_trading", "NVDA")]


def test_quiver_loop_agent_executes_exactly_one_ticker_scoped_tool_per_turn():
    llm = FakeToolLLM(
        responses=[
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "get_live_insider_trading",
                            "arguments": '{"ticker":"MSFT"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {
                            "name": "get_live_congress_trading",
                            "arguments": '{"ticker":"NVDA"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": '{"outcome":"watchlist","summary":"Mixed evidence.","items":[{"ticker":"MSFT","action":"watch","conviction_score":0.61,"supporting_evidence":["Insider buy"],"opposing_evidence":["Conflicting thesis"],"risk_notes":["Needs more confirmation"],"source_summary":["Mixed evidence"],"broker_eligible":true}]}',
                "tool_calls": [],
            },
        ]
    )
    quiver_client = StubQuiverClient()
    agent = QuiverLoopAgent(
        llm=llm,
        budget=ResearchAgentBudget(max_steps=4, max_tool_calls=3, max_seed_tickers=2),
    )

    result = agent.run(
        run_id="run-456",
        evidence_bundles=[_bundle("MSFT", supporting_count=2), _bundle("NVDA", supporting_count=1)],
        account_context={"buying_power": "1000"},
        quiver_client=quiver_client,
    )

    assert result.stop_reason == "final_answer"
    assert result.tool_call_count == 2
    assert quiver_client.calls == [
        ("get_live_insider_trading", "MSFT"),
        ("get_live_congress_trading", "NVDA"),
    ]
    assert len(result.trace) == 3
    assert result.trace[0].tool_name == "get_live_insider_trading"
    assert result.trace[1].tool_name == "get_live_congress_trading"
    assert result.trace[2].action == "finalize"


def test_quiver_loop_agent_returns_explicit_stop_reasons_for_empty_seed_and_budget_exhaustion():
    empty_agent = QuiverLoopAgent(
        llm=FakeToolLLM(responses=[]),
        budget=ResearchAgentBudget(max_steps=2, max_tool_calls=1, max_seed_tickers=2),
    )

    empty_result = empty_agent.run(
        run_id="run-empty",
        evidence_bundles=[],
        account_context={"buying_power": "1000"},
        quiver_client=StubQuiverClient(),
    )

    assert empty_result.stop_reason == "empty_ticker_set"
    assert empty_result.tool_call_count == 0
    assert empty_result.investigated_tickers == []
    assert empty_result.outcome.outcome == "no_action"

    budget_agent = QuiverLoopAgent(
        llm=FakeToolLLM(
            responses=[
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "get_live_congress_trading",
                                "arguments": '{"ticker":"NVDA"}',
                            },
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-2",
                            "type": "function",
                            "function": {
                                "name": "get_live_insider_trading",
                                "arguments": '{"ticker":"NVDA"}',
                            },
                        }
                    ],
                },
            ]
        ),
        budget=ResearchAgentBudget(max_steps=3, max_tool_calls=1, max_seed_tickers=1),
    )

    budget_result = budget_agent.run(
        run_id="run-budget",
        evidence_bundles=[_bundle("NVDA", supporting_count=1)],
        account_context={"buying_power": "1000"},
        quiver_client=StubQuiverClient(),
    )

    assert budget_result.stop_reason == "budget_exhausted"
    assert budget_result.tool_call_count == 1
    assert budget_result.investigated_tickers == ["NVDA"]
    assert budget_result.outcome.outcome == "no_action"
