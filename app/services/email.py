from app.schemas.workflow import RecommendationEmail


def compose_recommendation_email(
    run_id: str,
    recommendations: list,
    approval_url: str,
    rejection_url: str,
) -> RecommendationEmail:
    tickers = ", ".join(item.ticker for item in recommendations)
    body = (
        f"Run {run_id}\n"
        f"Recommendations: {tickers}\n"
        f"Approve: {approval_url}\n"
        f"Reject: {rejection_url}"
    )
    return RecommendationEmail(
        subject=f"Investor review for {run_id}",
        body=body,
    )


def send_console_email(message: RecommendationEmail) -> RecommendationEmail:
    return message
