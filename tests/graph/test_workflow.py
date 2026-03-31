from types import SimpleNamespace

from app.graph.runtime import InvestorRuntime
from app.graph.workflow import compile_workflow
from app.schemas.quiver import CongressionalTrade, TickerEvidenceBundle
from app.schemas.research import CandidateOutcome, CandidateRecommendation, NoActionOutcome
from app.services.tokens import verify_approval_token


class StubResearchNode:
    def __init__(self) -> None:
        self.calls = []

    def run(self, run_id: str, evidence_bundles: list[TickerEvidenceBundle], account_context: dict[str, str]):
        self.calls.append((run_id, evidence_bundles, account_context))
        return CandidateOutcome(
            outcome="candidates",
            recommendations=[
                CandidateRecommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.81,
                    supporting_evidence=["Congress buy", "Insider buy"],
                    opposing_evidence=[],
                    risk_notes=["Volatile"],
                    source_summary=["Signals aligned"],
                    broker_eligible=False,
                )
            ],
        )


class StubQuiverClient:
    def __init__(self) -> None:
        self.calls = []

    def get_live_congress_trading(self):
        self.calls.append("congress")
        return [CongressionalTrade(Ticker="NVDA", Transaction="Purchase")]

    def get_live_insider_trading(self):
        self.calls.append("insiders")
        return []

    def get_live_government_contracts(self):
        self.calls.append("gov_contracts")
        return []

    def get_live_lobbying(self):
        self.calls.append("lobbying")
        return []


class MailProviderSpy:
    def __init__(self) -> None:
        self.calls = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.calls.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


def make_settings():
    return SimpleNamespace(
        app_secret="test-secret",
        approval_token_ttl_seconds=900,
        external_base_url="https://investor.example.com",
        daily_memo_to_email="operator@example.com",
        database_url="postgresql://example",
        langgraph_checkpointer_url=None,
    )


def test_workflow_pauses_for_human_review():
    research_node = StubResearchNode()
    quiver_client = StubQuiverClient()
    mail_provider = MailProviderSpy()
    compiled_graph = compile_workflow(
        research_node=research_node,
        settings=make_settings(),
        mail_provider=mail_provider,
        evidence_builder=lambda **_: [
            TickerEvidenceBundle(ticker="NVDA", supporting_signals=[], contradictory_signals=[], source_summary=["Signals aligned"])
        ],
    )

    result = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "buying_power": "1000",
            "quiver_client": quiver_client,
        }
    )

    assert result["status"] == "awaiting_human_review"
    assert quiver_client.calls == ["congress", "insiders", "gov_contracts", "lobbying"]
    assert result["evidence_bundles"][0].ticker == "NVDA"
    assert result["finalized_outcome"].outcome == "candidates"
    assert result["recommendations"][0].ticker == "NVDA"
    assert research_node.calls[0][0] == "run-123"
    assert mail_provider.calls[0]["recipient"] == "operator@example.com"


def test_workflow_resumes_to_handoff_after_approval():
    compiled_graph = compile_workflow(
        research_node=StubResearchNode(),
        settings=make_settings(),
        mail_provider=MailProviderSpy(),
        evidence_builder=lambda **_: [
            TickerEvidenceBundle(ticker="NVDA", supporting_signals=[], contradictory_signals=[], source_summary=["Signals aligned"])
        ],
    )
    paused = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "buying_power": "1000",
            "quiver_client": StubQuiverClient(),
        }
    )

    resumed = compiled_graph.resume(paused, decision="approve")

    assert resumed["status"] == "completed"
    assert resumed["handoff"]["run_id"] == "run-123"


def test_workflow_email_uses_signed_links_from_state():
    settings = make_settings()
    mail_provider = MailProviderSpy()
    compiled_graph = compile_workflow(
        research_node=StubResearchNode(),
        settings=settings,
        mail_provider=mail_provider,
        evidence_builder=lambda **_: [
            TickerEvidenceBundle(ticker="NVDA", supporting_signals=[], contradictory_signals=[], source_summary=["Signals aligned"])
        ],
    )

    paused = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "buying_power": "1000",
            "quiver_client": StubQuiverClient(),
        }
    )

    sent_message = mail_provider.calls[0]
    assert "Ranked Candidates" in paused["email_body"]
    assert "https://investor.example.com/approval/" in paused["email_body"]
    assert "run-123:approve" not in paused["email_body"]
    assert "https://investor.example.com/approval/" in sent_message["text_body"]

    approve_token = sent_message["text_body"].split("Approve: https://investor.example.com/approval/")[1].splitlines()[0]
    reject_token = sent_message["text_body"].split("Reject: https://investor.example.com/approval/")[1].splitlines()[0]

    assert verify_approval_token(approve_token, settings.app_secret, settings.approval_token_ttl_seconds).decision == "approve"
    assert verify_approval_token(reject_token, settings.app_secret, settings.approval_token_ttl_seconds).decision == "reject"


def test_workflow_resume_uses_empty_recommendations_for_no_action():
    class NoActionResearchNode:
        def run(self, run_id: str, evidence_bundles: list[TickerEvidenceBundle], account_context: dict[str, str]):
            return NoActionOutcome(
                outcome="no_action",
                summary="No qualifying ideas.",
                reasons=["No candidates survived deterministic pruning."],
            )

    compiled_graph = compile_workflow(
        research_node=NoActionResearchNode(),
        settings=make_settings(),
        mail_provider=MailProviderSpy(),
        evidence_builder=lambda **_: [
            TickerEvidenceBundle(ticker="NVDA", supporting_signals=[], contradictory_signals=[], source_summary=["Signals aligned"])
        ],
    )

    paused = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "buying_power": "1000",
            "quiver_client": StubQuiverClient(),
        }
    )
    resumed = compiled_graph.resume(paused, decision="approve")

    assert paused["recommendations"] == []
    assert resumed["handoff"]["recommendations"] == []


def test_runtime_bootstraps_postgres_checkpointer_and_reuses_thread_id():
    calls: list[tuple[str, str]] = []

    class FakeCheckpointer:
        def __init__(self) -> None:
            self.setup_calls = 0

        def setup(self) -> None:
            self.setup_calls += 1

    class FakeWorkflow:
        def invoke(self, state: dict) -> dict:
            calls.append(("invoke", state["thread_id"]))
            return {**state, "status": "awaiting_human_review", "recommendations": []}

        def resume(self, state: dict, decision: str) -> dict:
            calls.append(("resume", state["thread_id"]))
            return {**state, "status": "completed", "decision": decision}

    checkpointer = FakeCheckpointer()
    runtime = InvestorRuntime(
        settings=SimpleNamespace(
            database_url="postgresql://example",
            langgraph_checkpointer_url=None,
            app_secret="secret",
            approval_token_ttl_seconds=900,
            external_base_url="https://investor.example.com",
            daily_memo_to_email="operator@example.com",
        ),
        workflow_factory=lambda research_node, settings, mail_provider, checkpointer, evidence_builder=None: FakeWorkflow(),
        checkpointer_factory=lambda conn: checkpointer,
    )

    paused = runtime.start_run(
        run_id="run-123",
        thread_id="thread-123",
        research_node=StubResearchNode(),
        quiver_client=StubQuiverClient(),
    )
    resumed = runtime.resume_run(paused, decision="approve", research_node=StubResearchNode())

    assert checkpointer.setup_calls == 1
    assert calls == [("invoke", "thread-123"), ("resume", "thread-123")]
    assert paused["status"] == "awaiting_human_review"
    assert resumed["status"] == "completed"
