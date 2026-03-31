from app.schemas.reports import StrategicInsightReport
from app.schemas.research import CandidateOutcome, CandidateRecommendation, NoActionOutcome, WatchlistOutcome
from app.services.report_builder import build_strategic_insight_report


def test_build_strategic_insight_report_classifies_immediate_defer_and_research_items():
    report = build_strategic_insight_report(
        run_id="run-123",
        outcome=CandidateOutcome(
            outcome="candidates",
            recommendations=[
                CandidateRecommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.91,
                    supporting_evidence=["Congress buy", "Insider accumulation"],
                    opposing_evidence=[],
                    risk_notes=["Valuation"],
                    source_summary=["AI demand remains strong"],
                    broker_eligible=True,
                ),
                CandidateRecommendation(
                    ticker="MSFT",
                    action="buy",
                    conviction_score=0.74,
                    supporting_evidence=["Contract backlog"],
                    opposing_evidence=[],
                    risk_notes=["Execution"],
                    source_summary=["Cloud demand steady"],
                    broker_eligible=True,
                ),
                CandidateRecommendation(
                    ticker="SHOP",
                    action="buy",
                    conviction_score=0.82,
                    supporting_evidence=["Lobbying tailwind"],
                    opposing_evidence=["Macro risk"],
                    risk_notes=["Competition"],
                    source_summary=["Merchant adoption improving"],
                    broker_eligible=False,
                ),
            ],
        ),
        baseline_run_id="run-122",
        baseline_outcome=CandidateOutcome(
            outcome="candidates",
            recommendations=[
                CandidateRecommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.8,
                    supporting_evidence=["Congress buy"],
                    opposing_evidence=[],
                    risk_notes=["Valuation"],
                    source_summary=["AI demand remains strong"],
                    broker_eligible=True,
                )
            ],
        ),
    )

    assert isinstance(report, StrategicInsightReport)
    assert [item.ticker for item in report.immediate_actions] == ["NVDA"]
    assert sorted(item.ticker for item in report.deferred_actions) == ["MSFT", "SHOP"]
    assert report.research_queue == []
    assert report.immediate_actions[0].operator_action == "Review for approval and paper-order prestage."
    assert all(
        item.operator_action == "Re-check on the next market session."
        for item in report.deferred_actions
    )
    assert report.headline == "1 immediate | 2 defer | 0 research"
    assert report.summary == "Compared against baseline run run-122; dropped tickers: none."


def test_build_strategic_insight_report_handles_watchlist_and_no_action_without_candidates():
    watchlist_report = build_strategic_insight_report(
        run_id="run-200",
        outcome=WatchlistOutcome(
            outcome="watchlist",
            summary="Signals are mixed and need more confirmation.",
            items=[
                CandidateRecommendation(
                    ticker="AMD",
                    action="watch",
                    conviction_score=0.55,
                    supporting_evidence=["Contract activity"],
                    opposing_evidence=["Margin pressure"],
                    risk_notes=["Competition"],
                    source_summary=["Need another session"],
                    broker_eligible=False,
                )
            ],
        ),
        baseline_run_id=None,
        baseline_outcome=None,
    )
    no_action_report = build_strategic_insight_report(
        run_id="run-201",
        outcome=NoActionOutcome(
            outcome="no_action",
            summary="No names cleared the bar.",
            reasons=["Breadth is weak."],
        ),
        baseline_run_id=None,
        baseline_outcome=None,
    )

    assert watchlist_report.immediate_actions == []
    assert watchlist_report.deferred_actions == []
    assert [item.ticker for item in watchlist_report.research_queue] == ["AMD"]
    assert watchlist_report.research_queue[0].operator_action == "Collect more Quiver evidence before approval."
    assert no_action_report.immediate_actions == []
    assert no_action_report.deferred_actions == []
    assert [item.ticker for item in no_action_report.research_queue] == ["RUN-201"]
    assert no_action_report.headline == "0 immediate | 0 defer | 1 research"
