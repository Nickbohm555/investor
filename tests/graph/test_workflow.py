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

    result = compiled_graph.invoke({"run_id": "run-123"})

    assert result["status"] == "awaiting_human_review"


def test_workflow_resumes_to_handoff_after_approval():
    compiled_graph = compile_workflow(research_node=StubResearchNode())
    paused = compiled_graph.invoke({"run_id": "run-123"})

    resumed = compiled_graph.resume(paused, decision="approve")

    assert resumed["status"] == "completed"
    assert resumed["handoff"]["run_id"] == "run-123"
