from app.schemas.research import CandidateOutcome, NoActionOutcome, ResearchOutcome, WatchlistOutcome
from app.schemas.workflow import DailyMemoContent, Recommendation, RecommendationEmail, WatchlistItem
from app.services.email import compose_recommendation_email
from app.services.handoff import build_alpaca_handoff
from app.services.quiver_normalize import build_ticker_evidence_bundles
from app.services.ranking import finalize_research_outcome
from app.services.tokens import sign_approval_token


class CompiledInvestorWorkflow:
    def __init__(self, research_node, settings, mail_provider, checkpointer=None, evidence_builder=build_ticker_evidence_bundles):
        self._research_node = research_node
        self._settings = settings
        self._mail_provider = mail_provider
        self._checkpointer = checkpointer
        self._evidence_builder = evidence_builder

    def invoke(self, state: dict) -> dict:
        evidence_bundles = self._build_evidence_bundles(state["quiver_client"])
        research_result = self._run_research(state, evidence_bundles)
        finalized_outcome = finalize_research_outcome(research_result)
        recommendations = finalized_outcome.recommendations if isinstance(finalized_outcome, CandidateOutcome) else []
        memo_content = self._build_memo_content(finalized_outcome)
        email = self._compose_email(state["run_id"], memo_content)
        self._mail_provider.send(
            subject=email.subject,
            text_body=email.body,
            html_body=email.html_body,
            recipient=self._settings.daily_memo_to_email,
        )
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

    def _build_evidence_bundles(self, quiver_client):
        return self._evidence_builder(
            congress=quiver_client.get_live_congress_trading(),
            insiders=quiver_client.get_live_insider_trading(),
            gov_contracts=quiver_client.get_live_government_contracts(),
            lobbying=quiver_client.get_live_lobbying(),
        )

    def _run_research(self, state: dict, evidence_bundles) -> ResearchOutcome:
        return self._research_node.run(
            run_id=state["run_id"],
            evidence_bundles=evidence_bundles,
            account_context=state,
        )

    def _compose_email(self, run_id: str, recommendations: DailyMemoContent) -> RecommendationEmail:
        return compose_recommendation_email(
            run_id=run_id,
            recommendations=recommendations,
            approval_url=self._build_approval_url(run_id, "approve"),
            rejection_url=self._build_approval_url(run_id, "reject"),
        )

    def _build_approval_url(self, run_id: str, decision: str) -> str:
        token = sign_approval_token(
            run_id=run_id,
            decision=decision,
            secret=self._settings.app_secret,
            ttl_seconds=self._settings.approval_token_ttl_seconds,
        )
        return f"{self._settings.external_base_url.rstrip('/')}/approval/{token}"

    def _build_memo_content(self, outcome: ResearchOutcome) -> DailyMemoContent:
        if isinstance(outcome, CandidateOutcome):
            return DailyMemoContent(
                recommendations=[
                    Recommendation(
                        ticker=item.ticker,
                        action=item.action,
                        conviction_score=item.conviction_score,
                        rationale=self._candidate_rationale(item),
                    )
                    for item in outcome.recommendations
                ]
            )
        if isinstance(outcome, WatchlistOutcome):
            return DailyMemoContent(
                watchlist=[
                    WatchlistItem(
                        ticker=item.ticker,
                        summary=item.source_summary[0] if item.source_summary else outcome.summary,
                    )
                    for item in outcome.items
                ]
            )
        if isinstance(outcome, NoActionOutcome):
            return DailyMemoContent(no_action_reasons=[outcome.summary, *outcome.reasons])
        raise TypeError(f"Unsupported outcome: {type(outcome)!r}")

    def _candidate_rationale(self, item) -> str:
        parts = []
        if item.supporting_evidence:
            parts.append(", ".join(item.supporting_evidence))
        if item.source_summary:
            parts.append(", ".join(item.source_summary))
        if item.risk_notes:
            parts.append(f"Risks: {', '.join(item.risk_notes)}")
        return "; ".join(parts)

    def _await_human_review(self, state: dict, message: RecommendationEmail) -> dict:
        persisted_state = {key: value for key, value in state.items() if key != "quiver_client"}
        return {
            **persisted_state,
            "status": "awaiting_review",
            "email_body": message.body,
        }


def compile_workflow(research_node, settings, mail_provider, checkpointer=None, evidence_builder=build_ticker_evidence_bundles) -> CompiledInvestorWorkflow:
    return CompiledInvestorWorkflow(
        research_node=research_node,
        settings=settings,
        mail_provider=mail_provider,
        checkpointer=checkpointer,
        evidence_builder=evidence_builder,
    )
