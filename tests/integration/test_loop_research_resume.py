from types import SimpleNamespace
from typing import Optional

from app.agents.research import ResearchNode
from app.graph.runtime import InvestorRuntime
from app.schemas.quiver import SignalRecord, TickerEvidenceBundle


class FakeToolLLM:
    def __init__(self) -> None:
        self._calls = 0

    def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        tool_choice: str = "auto",
        parallel_tool_calls: bool = False,
    ) -> dict[str, object]:
        self._calls += 1
        if self._calls == 1:
            return {
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
            }
        return {
            "role": "assistant",
            "content": '{"outcome":"candidates","recommendations":[{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy"],"opposing_evidence":[],"risk_notes":["Volatile"],"source_summary":["Signals aligned"],"broker_eligible":true}]}',
            "tool_calls": [],
        }


class StubQuiverClient:
    def get_live_congress_trading(self, ticker: Optional[str] = None):
        return []

    def get_live_insider_trading(self, ticker: Optional[str] = None):
        return []

    def get_live_government_contracts(self, ticker: Optional[str] = None):
        return []

    def get_live_lobbying(self, ticker: Optional[str] = None):
        return []


class MailProviderSpy:
    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        return None


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
            source_summary=["Signals aligned"],
        )
    ]


def test_investor_runtime_preserves_trace_metadata_through_start_and_resume():
    research_node = ResearchNode(llm=FakeToolLLM())
    runtime = InvestorRuntime(
        settings=SimpleNamespace(
            app_secret="test-secret",
            approval_token_ttl_seconds=900,
            external_base_url="https://investor.example.com",
            daily_memo_to_email="operator@example.com",
        ),
        mail_provider=MailProviderSpy(),
        workflow_factory=lambda research_node, settings, mail_provider: __import__(
            "app.graph.workflow", fromlist=["compile_workflow"]
        ).compile_workflow(
            research_node=research_node,
            settings=settings,
            mail_provider=mail_provider,
            evidence_builder=lambda **_: _bundle(),
        ),
    )

    started = runtime.start_run(
        run_id="run-123",
        research_node=research_node,
        quiver_client=StubQuiverClient(),
    )
    resumed = runtime.resume_run(started, decision="approve", research_node=research_node)

    assert started["research_trace"][0]["tool_name"] == "get_live_congress_trading"
    assert started["research_stop_reason"] == "final_answer"
    assert started["research_tool_call_count"] == 1
    assert started["investigated_tickers"] == ["NVDA"]
    assert resumed["research_trace"][0]["tool_name"] == "get_live_congress_trading"
    assert resumed["status"] == "broker_prestaged"
