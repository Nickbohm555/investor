from __future__ import annotations

from types import SimpleNamespace

from app.graph.workflow import CompiledInvestorWorkflow
from app.schemas.research import NoActionOutcome, WatchlistOutcome


class _MailProviderSpy:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        self.sent_messages.append(
            {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "recipient": recipient,
            }
        )


class _QuiverClientStub:
    def get_live_congress_trading(self):
        return []

    def get_live_insider_trading(self):
        return []

    def get_live_government_contracts(self):
        return []

    def get_live_lobbying(self):
        return []


class _ResearchNodeStub:
    def __init__(self, outcome) -> None:
        self._outcome = outcome

    def run_with_trace(self, **kwargs):
        return SimpleNamespace(
            outcome=self._outcome,
            trace=[],
            stop_reason="complete",
            tool_call_count=0,
            investigated_tickers=[],
        )


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        app_secret="secret",
        approval_token_ttl_seconds=900,
        external_base_url="https://example.test",
        daily_memo_to_email="operator@example.test",
    )


def _invoke(outcome, run_id: str) -> dict:
    workflow = CompiledInvestorWorkflow(
        research_node=_ResearchNodeStub(outcome),
        settings=_settings(),
        mail_provider=_MailProviderSpy(),
        evidence_builder=lambda **kwargs: [],
    )
    return workflow.invoke(
        {
            "run_id": run_id,
            "quiver_client": _QuiverClientStub(),
        }
    )


def test_workflow_persists_named_research_queue_guidance_fields_on_strategic_report() -> None:
    watchlist_state = _invoke(
        WatchlistOutcome(
            outcome="watchlist",
            summary="Signals remain mixed.",
            items=[
                {
                    "ticker": "msft",
                    "action": "watch",
                    "conviction_score": 0.42,
                    "supporting_evidence": ["Congress buying increased."],
                    "opposing_evidence": ["Insider sales picked up."],
                    "risk_notes": ["Need more evidence."],
                    "source_summary": ["Mixed Quiver activity."],
                    "broker_eligible": False,
                    "watchlist_reason": "Conflicting conviction after mixed insider and contract signals.",
                    "missing_evidence": ["Need two independent supporting filings."],
                    "unresolved_questions": ["Did the contract award recur across quarters?"],
                    "next_steps": ["Check the next Quiver contracts refresh for repeat awards."],
                }
            ],
        ),
        "run-14-watchlist",
    )
    no_action_state = _invoke(
        NoActionOutcome(
            outcome="no_action",
            summary="Nothing cleared the threshold.",
            reasons=["Signals were stale."],
        ),
        "run-14-no-action",
    )

    watchlist_payload = watchlist_state["strategic_report"]["research_queue"][0]
    no_action_payload = no_action_state["strategic_report"]["research_queue"][0]

    for payload in (watchlist_payload, no_action_payload):
        assert "watchlist_reason" in payload
        assert "missing_evidence" in payload
        assert "unresolved_questions" in payload
        assert "next_steps" in payload
