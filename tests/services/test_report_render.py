from app.schemas.reports import DeferredActionItem, ImmediateActionItem, ResearchNeededItem, StrategicInsightReport
from app.services.report_render import render_report_email


def test_render_report_email_outputs_bucket_sections_and_links():
    email = render_report_email(
        report=StrategicInsightReport(
            run_id="run-123",
            baseline_run_id="run-122",
            headline="1 immediate | 1 defer | 1 research",
            summary="Compared against baseline run run-122; dropped tickers: AMD.",
            immediate_actions=[
                ImmediateActionItem(
                    ticker="NVDA",
                    thesis="AI demand remains strong",
                    change_summary="conviction increased",
                    why_now="Congress buy; Insider accumulation",
                    operator_action="Review for approval and paper-order prestage.",
                )
            ],
            deferred_actions=[
                DeferredActionItem(
                    ticker="MSFT",
                    thesis="Cloud demand steady",
                    change_summary="signal mix unchanged",
                    defer_reason="Conviction below immediate threshold of 0.75.",
                    operator_action="Re-check on the next market session.",
                )
            ],
            research_queue=[
                ResearchNeededItem(
                    ticker="AMD",
                    thesis="Need another session",
                    uncertainty="Signals remain mixed.",
                    follow_up_questions=["What changed in contracts?"],
                    operator_action="Collect more Quiver evidence before approval.",
                )
            ],
            dropped_tickers=["AMD"],
        ),
        approval_url="https://investor.example.com/approval/approve-token",
        rejection_url="https://investor.example.com/approval/reject-token",
    )

    assert "Strategic Insight Report" in email.body
    assert "Immediate Actions" in email.body
    assert "Deferred" in email.body
    assert "Research Queue" in email.body
    assert "Dropped Since Last Delivered Run" in email.body
    assert "Approve: https://investor.example.com/approval/approve-token" in email.body
    assert "Reject: https://investor.example.com/approval/reject-token" in email.body
    assert "<h1>Strategic Insight Report</h1>" in email.html_body
    assert "<h2>Immediate Actions</h2>" in email.html_body
    assert "<h2>Deferred</h2>" in email.html_body
    assert "<h2>Research Queue</h2>" in email.html_body
    assert 'href="https://investor.example.com/approval/approve-token"' in email.html_body
    assert 'href="https://investor.example.com/approval/reject-token"' in email.html_body


def test_render_report_email_includes_dropped_tickers_and_research_queue():
    email = render_report_email(
        report=StrategicInsightReport(
            run_id="run-789",
            baseline_run_id=None,
            headline="0 immediate | 0 defer | 1 research",
            summary="Compared against no prior delivered run; dropped tickers: none.",
            research_queue=[
                ResearchNeededItem(
                    ticker="SHOP",
                    thesis="Merchant adoption improving",
                    uncertainty="Need more evidence.",
                    follow_up_questions=["Did insider activity improve?"],
                    operator_action="Collect more Quiver evidence before approval.",
                )
            ],
            dropped_tickers=["AMD"],
        ),
        approval_url="https://investor.example.com/approval/approve-token",
        rejection_url="https://investor.example.com/approval/reject-token",
    )

    assert "Dropped Since Last Delivered Run" in email.body
    assert "AMD" in email.body
    assert "Research Queue" in email.body
    assert "SHOP" in email.body
