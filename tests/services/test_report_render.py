from __future__ import annotations

from app.schemas.reports import ResearchNeededItem, StrategicInsightReport
from app.services.report_render import render_report_email


def _report(*, research_queue: list[ResearchNeededItem]) -> StrategicInsightReport:
    return StrategicInsightReport(
        run_id="run-14",
        headline="0 immediate | 0 defer | 1 research",
        summary="Compared against no prior delivered run; dropped tickers: none.",
        research_queue=research_queue,
    )


def test_render_report_email_outputs_named_research_queue_guidance_sections() -> None:
    email = render_report_email(
        report=_report(
            research_queue=[
                ResearchNeededItem(
                    ticker="MSFT",
                    thesis="Mixed signal stack.",
                    watchlist_reason="Conflicting conviction after mixed insider and contract signals.",
                    missing_evidence=["Need two independent supporting filings."],
                    unresolved_questions=["Did the contract award recur across quarters?"],
                    next_steps=["Check the next Quiver contracts refresh for repeat awards."],
                    operator_action="Do not approve yet. Resolve the listed evidence gaps first.",
                )
            ]
        ),
        approval_url="https://example.test/approve",
        rejection_url="https://example.test/reject",
    )

    assert "Why Not Actionable Yet:" in email.body
    assert "Missing Evidence:" in email.body
    assert "Open Questions:" in email.body
    assert "Next Checks:" in email.body
    assert "Action:" in email.body


def test_render_report_email_outputs_research_queue_guidance_in_html() -> None:
    email = render_report_email(
        report=_report(
            research_queue=[
                ResearchNeededItem(
                    ticker="MSFT",
                    thesis="Mixed signal stack.",
                    watchlist_reason="Conflicting conviction after mixed insider and contract signals.",
                    missing_evidence=["Need two independent supporting filings."],
                    unresolved_questions=["Did the contract award recur across quarters?"],
                    next_steps=["Check the next Quiver contracts refresh for repeat awards."],
                    operator_action="Do not approve yet. Resolve the listed evidence gaps first.",
                )
            ]
        ),
        approval_url="https://example.test/approve",
        rejection_url="https://example.test/reject",
    )

    assert "Why Not Actionable Yet:" in email.html_body
    assert "Missing Evidence:" in email.html_body
    assert "Open Questions:" in email.html_body
    assert "Next Checks:" in email.html_body


def test_render_report_email_outputs_no_action_guidance_with_neutral_labels() -> None:
    email = render_report_email(
        report=_report(
            research_queue=[
                ResearchNeededItem(
                    ticker="RUN-14",
                    thesis="Nothing cleared the threshold.",
                    watchlist_reason="Nothing cleared the threshold.",
                    missing_evidence=["Signals were stale."],
                    unresolved_questions=[],
                    next_steps=["Wait for materially new Quiver evidence before reconsidering."],
                    operator_action="Wait for materially new evidence before reconsidering.",
                )
            ]
        ),
        approval_url="https://example.test/approve",
        rejection_url="https://example.test/reject",
    )

    assert "Why Not Actionable Yet:" in email.body
    assert "Missing Evidence:" in email.body
    assert "Open Questions:" in email.body
    assert "Next Checks:" in email.body
    assert "RUN-14 | Nothing cleared the threshold." in email.body
