from html import escape

from app.schemas.reports import StrategicInsightReport
from app.schemas.workflow import DailyMemoContent, RecommendationEmail


def compose_recommendation_email(
    run_id: str,
    recommendations: DailyMemoContent,
    approval_url: str,
    rejection_url: str,
) -> RecommendationEmail:
    body = [f"Run {run_id}"]
    html_parts = [f"<p>Run {escape(run_id)}</p>"]

    if recommendations.recommendations:
        body.append("Ranked Candidates")
        html_parts.append("<h2>Ranked Candidates</h2>")
        for item in recommendations.recommendations:
            body.append(f"{item.ticker} | {item.action} | conviction={item.conviction_score:.2f}")
            body.append(item.rationale)
            html_parts.append(
                "<p>"
                f"{escape(item.ticker)} | {escape(item.action)} | conviction={item.conviction_score:.2f}<br>"
                f"{escape(item.rationale)}"
                "</p>"
            )
    elif recommendations.watchlist:
        body.append("Watchlist")
        html_parts.append("<h2>Watchlist</h2>")
        for item in recommendations.watchlist:
            body.append(f"{item.ticker} | {item.summary}")
            html_parts.append(f"<p>{escape(item.ticker)} | {escape(item.summary)}</p>")
    else:
        body.append("No Action")
        html_parts.append("<h2>No Action</h2>")
        body.extend(recommendations.no_action_reasons)
        for reason in recommendations.no_action_reasons:
            html_parts.append(f"<p>{escape(reason)}</p>")

    body.append(f"Approve: {approval_url}")
    body.append(f"Reject: {rejection_url}")
    html_parts.append(f"<p>Approve: <a href=\"{escape(approval_url)}\">{escape(approval_url)}</a></p>")
    html_parts.append(f"<p>Reject: <a href=\"{escape(rejection_url)}\">{escape(rejection_url)}</a></p>")
    return RecommendationEmail(
        subject=f"Investor review for {run_id}",
        body="\n".join(body),
        html_body="".join(html_parts),
    )


def compose_report_email(
    *, report: StrategicInsightReport, approval_url: str, rejection_url: str
) -> RecommendationEmail:
    raise NotImplementedError
