from types import SimpleNamespace

from app.graph.runtime import InvestorRuntime
from app.graph.workflow import compile_workflow
from app.schemas.workflow import Recommendation, ResearchResult


class StubResearchNode:
    def run(self, account_context: dict[str, str]) -> ResearchResult:
        return ResearchResult(
            recommendations=[
                Recommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.81,
                    rationale="signal",
                )
            ]
        )


def test_workflow_pauses_for_human_review():
    compiled_graph = compile_workflow(research_node=StubResearchNode())

    result = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "approval_url": "http://testserver/approval/approve-token",
            "rejection_url": "http://testserver/approval/reject-token",
        }
    )

    assert result["status"] == "awaiting_human_review"


def test_workflow_resumes_to_handoff_after_approval():
    compiled_graph = compile_workflow(research_node=StubResearchNode())
    paused = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "approval_url": "http://testserver/approval/approve-token",
            "rejection_url": "http://testserver/approval/reject-token",
        }
    )

    resumed = compiled_graph.resume(paused, decision="approve")

    assert resumed["status"] == "completed"
    assert resumed["handoff"]["run_id"] == "run-123"


def test_workflow_email_uses_signed_links_from_state():
    compiled_graph = compile_workflow(research_node=StubResearchNode())

    paused = compiled_graph.invoke(
        {
            "run_id": "run-123",
            "approval_url": "http://testserver/approval/signed-approve-token",
            "rejection_url": "http://testserver/approval/signed-reject-token",
        }
    )

    assert "signed-approve-token" in paused["email_body"]
    assert "signed-reject-token" in paused["email_body"]
    assert "run-123:approve" not in paused["email_body"]


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
        ),
        workflow_factory=lambda research_node, checkpointer: FakeWorkflow(),
        checkpointer_factory=lambda conn: checkpointer,
    )

    paused = runtime.start_run(
        run_id="run-123",
        thread_id="thread-123",
        research_node=StubResearchNode(),
        base_url="http://testserver",
    )
    resumed = runtime.resume_run(paused, decision="approve", research_node=StubResearchNode())

    assert checkpointer.setup_calls == 1
    assert calls == [("invoke", "thread-123"), ("resume", "thread-123")]
    assert paused["status"] == "awaiting_human_review"
    assert resumed["status"] == "completed"
