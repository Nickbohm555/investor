from app.schemas.workflow import RecommendationEmail, ResearchResult
from app.services.email import compose_recommendation_email, send_console_email
from app.services.handoff import build_alpaca_handoff
from app.services.risk import filter_recommendations


class CompiledInvestorWorkflow:
    def __init__(self, research_node):
        self._research_node = research_node

    def invoke(self, state: dict) -> dict:
        research_result = self._run_research(state)
        recommendations = self._risk_filter(research_result)
        email = self._compose_email(state["run_id"], recommendations)
        send_console_email(email)
        return self._await_human_review(
            {**state, "recommendations": recommendations},
            email,
        )

    def resume(self, state: dict, decision: str) -> dict:
        if decision != "approve":
            return {**state, "status": "rejected"}
        handed_off = {
            **state,
            "handoff": build_alpaca_handoff(state["run_id"], state["recommendations"]),
        }
        return {**handed_off, "status": "completed"}

    def _run_research(self, state: dict) -> ResearchResult:
        return self._research_node.run(account_context={"run_id": state["run_id"]})

    def _risk_filter(self, result: ResearchResult) -> list:
        return filter_recommendations(result.recommendations, minimum_conviction=0.6, max_ideas=3)

    def _compose_email(self, run_id: str, recommendations: list[object]) -> RecommendationEmail:
        return compose_recommendation_email(
            run_id=run_id,
            recommendations=recommendations,
            approval_url=f"http://localhost:8000/approval/{run_id}:approve",
            rejection_url=f"http://localhost:8000/approval/{run_id}:reject",
        )

    def _await_human_review(self, state: dict, message: RecommendationEmail) -> dict:
        return {
            **state,
            "status": "awaiting_human_review",
            "email_body": message.body,
        }


def compile_workflow(research_node) -> CompiledInvestorWorkflow:
    return CompiledInvestorWorkflow(research_node=research_node)
