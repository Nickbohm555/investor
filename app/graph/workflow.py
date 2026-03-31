from app.schemas.research import CandidateOutcome, ResearchOutcome
from app.schemas.workflow import RecommendationEmail
from app.services.quiver_normalize import build_ticker_evidence_bundles
from app.services.email import compose_recommendation_email, send_console_email
from app.services.handoff import build_alpaca_handoff
from app.services.ranking import finalize_research_outcome


class CompiledInvestorWorkflow:
    def __init__(self, research_node, quiver_client, checkpointer=None, evidence_builder=build_ticker_evidence_bundles):
        self._research_node = research_node
        self._quiver_client = quiver_client
        self._checkpointer = checkpointer
        self._evidence_builder = evidence_builder

    def invoke(self, state: dict) -> dict:
        evidence_bundles = self._build_evidence_bundles()
        research_result = self._run_research(state, evidence_bundles)
        finalized_outcome = finalize_research_outcome(research_result)
        recommendations = finalized_outcome.recommendations if isinstance(finalized_outcome, CandidateOutcome) else []
        email = self._compose_email(
            state["run_id"],
            finalized_outcome,
            approval_url=state["approval_url"],
            rejection_url=state["rejection_url"],
        )
        send_console_email(email)
        return self._await_human_review(
            {
                **state,
                "evidence_bundles": evidence_bundles,
                "finalized_outcome": finalized_outcome,
                "recommendations": recommendations,
            },
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

    def _build_evidence_bundles(self):
        return self._evidence_builder(
            congress=self._quiver_client.get_live_congress_trading(),
            insiders=self._quiver_client.get_live_insider_trading(),
            gov_contracts=self._quiver_client.get_live_government_contracts(),
            lobbying=self._quiver_client.get_live_lobbying(),
        )

    def _run_research(self, state: dict, evidence_bundles) -> ResearchOutcome:
        return self._research_node.run(
            run_id=state["run_id"],
            evidence_bundles=evidence_bundles,
            account_context=state,
        )

    def _compose_email(
        self,
        run_id: str,
        outcome: ResearchOutcome,
        *,
        approval_url: str,
        rejection_url: str,
    ) -> RecommendationEmail:
        return compose_recommendation_email(
            run_id=run_id,
            outcome=outcome,
            approval_url=approval_url,
            rejection_url=rejection_url,
        )

    def _await_human_review(self, state: dict, message: RecommendationEmail) -> dict:
        return {
            **state,
            "status": "awaiting_human_review",
            "email_body": message.body,
        }


def compile_workflow(research_node, quiver_client, checkpointer=None, evidence_builder=build_ticker_evidence_bundles) -> CompiledInvestorWorkflow:
    return CompiledInvestorWorkflow(
        research_node=research_node,
        quiver_client=quiver_client,
        checkpointer=checkpointer,
        evidence_builder=evidence_builder,
    )
