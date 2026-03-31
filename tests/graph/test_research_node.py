import pytest
from typing import Optional

from app.agents.research import ResearchNode
from app.schemas.quiver import SignalRecord, TickerEvidenceBundle
from app.schemas.research_agent import AgentTraceStep, ResearchExecutionResult


class FakeListLLM:
    def __init__(self, responses: list[str]):
        self._responses = responses
        self.payloads: list[dict[str, str]] = []

    def invoke(self, payload: dict[str, str]) -> str:
        self.payloads.append(payload)
        return self._responses.pop(0)


class FakeToolLLM:
    def __init__(self, responses: list[dict[str, object]]):
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

    def get_live_congress_trading(self, ticker: Optional[str] = None):
        self.calls.append(("get_live_congress_trading", ticker))
        return []

    def get_live_insider_trading(self, ticker: Optional[str] = None):
        self.calls.append(("get_live_insider_trading", ticker))
        return []

    def get_live_government_contracts(self, ticker: Optional[str] = None):
        self.calls.append(("get_live_government_contracts", ticker))
        return []

    def get_live_lobbying(self, ticker: Optional[str] = None):
        self.calls.append(("get_live_lobbying", ticker))
        return []


def _bundle() -> list[TickerEvidenceBundle]:
    return [
        TickerEvidenceBundle(
            ticker="NVDA",
            supporting_signals=[
                SignalRecord(
                    signal_type="congress",
                    ticker="NVDA",
                    direction="positive",
                    magnitude_note="Congress purchase",
                    source_note="Congress buy",
                )
            ],
            contradictory_signals=[],
            source_summary=["Congress and insider signals aligned"],
        )
    ]


def test_research_node_parses_candidate_outcome():
    llm = FakeListLLM(
        responses=[
            '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Congress and insider signals aligned"],"broker_eligible":true}]}'
        ]
    )
    node = ResearchNode(
        llm=llm,
        prompt_builder=lambda run_id, evidence_bundles, account_context: {
            "system": f"Run {run_id}",
            "user": f"{evidence_bundles[0].ticker} {account_context['buying_power']}",
        },
    )

    result = node.run(
        run_id="run-123",
        evidence_bundles=_bundle(),
        account_context={"buying_power": "1000"},
    )

    assert result.outcome == "candidates"
    assert result.recommendations[0].supporting_evidence == ["Congress buy"]
    assert llm.payloads == [{"system": "Run run-123", "user": "NVDA 1000"}]


def test_research_node_parses_watchlist_outcome():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"outcome":"watchlist","summary":"Signals are mixed.","items":[{"ticker":"NVDA","action":"watch","conviction_score":0.64,"supporting_evidence":["Insider buy"],"opposing_evidence":["Lobbying risk"],"risk_notes":["Conflicting signals"],"source_summary":["Signals diverged"],"broker_eligible":true}]}'
            ]
        ),
        prompt_builder=lambda run_id, evidence_bundles, account_context: {
            "system": run_id,
            "user": evidence_bundles[0].ticker + account_context["buying_power"],
        },
    )

    result = node.run(
        run_id="run-123",
        evidence_bundles=_bundle(),
        account_context={"buying_power": "1000"},
    )

    assert result.outcome == "watchlist"
    assert result.items[0].opposing_evidence == ["Lobbying risk"]


def test_research_node_parses_no_action_outcome():
    node = ResearchNode(
        llm=FakeListLLM(
            responses=[
                '{"outcome":"no_action","summary":"No qualified ideas.","reasons":["No candidates survived pruning."]}'
            ]
        ),
        prompt_builder=lambda run_id, evidence_bundles, account_context: {
            "system": run_id,
            "user": evidence_bundles[0].ticker + account_context["buying_power"],
        },
    )

    result = node.run(
        run_id="run-123",
        evidence_bundles=_bundle(),
        account_context={"buying_power": "1000"},
    )

    assert result.outcome == "no_action"
    assert result.reasons == ["No candidates survived pruning."]


def test_research_node_raises_for_invalid_outcome_shape():
    node = ResearchNode(
        llm=FakeListLLM(responses=['{"outcome":"candidates","recommendations":[{"ticker":"NVDA"}]}']),
        prompt_builder=lambda run_id, evidence_bundles, account_context: {
            "system": run_id,
            "user": evidence_bundles[0].ticker + account_context["buying_power"],
        },
    )

    with pytest.raises(Exception):
        node.run(
            run_id="run-123",
            evidence_bundles=_bundle(),
            account_context={"buying_power": "1000"},
        )


def test_research_node_run_with_trace_returns_execution_result_and_run_stays_backward_compatible():
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
                "content": '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Signals aligned"],"broker_eligible":true}]}',
                "tool_calls": [],
            },
        ]
    )
    node = ResearchNode(llm=llm)

    execution = node.run_with_trace(
        run_id="run-123",
        evidence_bundles=_bundle(),
        account_context={"buying_power": "1000"},
        quiver_client=StubQuiverClient(),
    )
    outcome = ResearchNode(
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
                    "content": '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Signals aligned"],"broker_eligible":true}]}',
                    "tool_calls": [],
                },
            ]
        )
    ).run(
        run_id="run-123",
        evidence_bundles=_bundle(),
        account_context={"buying_power": "1000"},
        quiver_client=StubQuiverClient(),
    )

    assert isinstance(execution, ResearchExecutionResult)
    assert execution.stop_reason == "final_answer"
    assert execution.tool_call_count == 1
    assert execution.investigated_tickers == ["NVDA"]
    assert execution.trace[0].tool_name == "get_live_congress_trading"
    assert outcome.outcome == "candidates"
