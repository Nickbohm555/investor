from pydantic import TypeAdapter

from app.schemas.research import CandidateOutcome, ResearchOutcome
from app.schemas.workflow import RecommendationEmail
from app.services.email import compose_report_email
from app.services.handoff import build_alpaca_handoff
from app.services.quiver_normalize import build_ticker_evidence_bundles
from app.services.ranking import finalize_research_outcome
from app.services.report_builder import build_strategic_insight_report
from app.services.research_trace import serialize_research_trace
from app.services.tokens import sign_approval_token

RESEARCH_OUTCOME_ADAPTER = TypeAdapter(ResearchOutcome)


class CompiledInvestorWorkflow:
    def __init__(self, research_node, settings, mail_provider, evidence_builder=build_ticker_evidence_bundles):
        self._research_node = research_node
        self._settings = settings
        self._mail_provider = mail_provider
        self._evidence_builder = evidence_builder

    def invoke(self, state: dict) -> dict:
        evidence_bundles = self._build_evidence_bundles(state["quiver_client"])
        research_execution = self._run_research(state, evidence_bundles)
        finalized_outcome = finalize_research_outcome(research_execution.outcome)
        recommendations = finalized_outcome.recommendations if isinstance(finalized_outcome, CandidateOutcome) else []
        baseline_report = state.get("baseline_report")
        baseline_outcome = (
            RESEARCH_OUTCOME_ADAPTER.validate_python(baseline_report["finalized_outcome"])
            if baseline_report
            else None
        )
        report = build_strategic_insight_report(
            run_id=state["run_id"],
            outcome=finalized_outcome,
            baseline_run_id=baseline_report["run_id"] if baseline_report else None,
            baseline_outcome=baseline_outcome,
        )
        email = self._compose_email(state["run_id"], report)
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
                "research_trace": serialize_research_trace(research_execution.trace),
                "research_stop_reason": research_execution.stop_reason,
                "research_tool_call_count": research_execution.tool_call_count,
                "investigated_tickers": research_execution.investigated_tickers,
                "finalized_outcome": finalized_outcome,
                "recommendations": recommendations,
                "strategic_report": report.model_dump(mode="python"),
                "baseline_run_id": report.baseline_run_id,
            },
            email,
        )

    def resume(self, state: dict, decision: str) -> dict:
        if decision != "approve":
            return {
                **state,
                "status": "rejected",
                "current_step": "rejected",
                "handoff": None,
            }
        handed_off = {
            **state,
            "handoff": build_alpaca_handoff(state["run_id"], state["recommendations"]),
        }
        return {
            **handed_off,
            "status": "broker_prestaged",
            "current_step": "broker_prestaged",
        }

    def _build_evidence_bundles(self, quiver_client):
        return self._evidence_builder(
            congress=quiver_client.get_live_congress_trading(),
            insiders=quiver_client.get_live_insider_trading(),
            gov_contracts=quiver_client.get_live_government_contracts(),
            lobbying=quiver_client.get_live_lobbying(),
        )

    def _run_research(self, state: dict, evidence_bundles):
        account_context = {
            key: str(value)
            for key, value in state.items()
            if key != "quiver_client"
        }
        return self._research_node.run_with_trace(
            run_id=state["run_id"],
            evidence_bundles=evidence_bundles,
            account_context=account_context,
            quiver_client=state["quiver_client"],
        )

    def _compose_email(self, run_id: str, report) -> RecommendationEmail:
        return compose_report_email(
            report=report,
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

    def _await_human_review(self, state: dict, message: RecommendationEmail) -> dict:
        persisted_state = {key: value for key, value in state.items() if key != "quiver_client"}
        return {
            **persisted_state,
            "status": "awaiting_review",
            "current_step": "awaiting_review",
            "email_body": message.body,
        }


def compile_workflow(research_node, settings, mail_provider, evidence_builder=build_ticker_evidence_bundles) -> CompiledInvestorWorkflow:
    return CompiledInvestorWorkflow(
        research_node=research_node,
        settings=settings,
        mail_provider=mail_provider,
        evidence_builder=evidence_builder,
    )
