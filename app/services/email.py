from app.schemas.reports import (
    DeferredActionItem,
    ImmediateActionItem,
    ResearchNeededItem,
    StrategicInsightReport,
)
from app.schemas.workflow import DailyMemoContent, RecommendationEmail
from app.services.report_render import render_report_email


def compose_recommendation_email(
    run_id: str,
    recommendations: DailyMemoContent,
    approval_url: str,
    rejection_url: str,
) -> RecommendationEmail:
    return render_report_email(
        report=_legacy_memo_to_report(run_id=run_id, recommendations=recommendations),
        approval_url=approval_url,
        rejection_url=rejection_url,
    )


def compose_report_email(*, report: StrategicInsightReport, approval_url: str, rejection_url: str) -> RecommendationEmail:
    return render_report_email(
        report=report,
        approval_url=approval_url,
        rejection_url=rejection_url,
    )


def _legacy_memo_to_report(*, run_id: str, recommendations: DailyMemoContent) -> StrategicInsightReport:
    if recommendations.recommendations:
        return StrategicInsightReport(
            run_id=run_id,
            headline=f"{len(recommendations.recommendations)} immediate | 0 defer | 0 research",
            summary="Compared against no prior delivered run; dropped tickers: none.",
            immediate_actions=[
                ImmediateActionItem(
                    ticker=item.ticker,
                    thesis=item.rationale,
                    change_summary="signal mix unchanged",
                    why_now=item.rationale,
                    operator_action="Review for approval and paper-order prestage.",
                )
                for item in recommendations.recommendations
            ],
        )
    if recommendations.watchlist:
        return StrategicInsightReport(
            run_id=run_id,
            headline=f"0 immediate | 0 defer | {len(recommendations.watchlist)} research",
            summary="Compared against no prior delivered run; dropped tickers: none.",
            research_queue=[
                ResearchNeededItem(
                    ticker=item.ticker,
                    thesis=item.summary,
                    uncertainty=item.summary,
                    follow_up_questions=[item.summary],
                    operator_action="Collect more Quiver evidence before approval.",
                )
                for item in recommendations.watchlist
            ],
        )
    return StrategicInsightReport(
        run_id=run_id,
        headline=f"0 immediate | 0 defer | {len(recommendations.no_action_reasons)} research",
        summary="Compared against no prior delivered run; dropped tickers: none.",
        research_queue=[
            ResearchNeededItem(
                ticker=run_id.upper(),
                thesis=recommendations.no_action_reasons[0],
                uncertainty=recommendations.no_action_reasons[0],
                follow_up_questions=recommendations.no_action_reasons,
                operator_action="Collect more Quiver evidence before approval.",
            )
        ]
        if recommendations.no_action_reasons
        else [],
    )
