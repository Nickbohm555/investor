from app.schemas.research import CandidateOutcome, NoActionOutcome, ResearchOutcome, WatchlistOutcome
from app.schemas.workflow import RecommendationEmail


def compose_recommendation_email(
    run_id: str,
    outcome: ResearchOutcome,
    approval_url: str,
    rejection_url: str,
) -> RecommendationEmail:
    body = [f"Run {run_id}"]

    if isinstance(outcome, CandidateOutcome):
        body.append("Ranked Candidates")
        for item in outcome.recommendations:
            body.append(
                f"{item.ticker} | {item.action} | conviction={item.conviction_score:.2f} | "
                f"supporting={', '.join(item.supporting_evidence)} | risks={', '.join(item.risk_notes)}"
            )
    elif isinstance(outcome, WatchlistOutcome):
        body.append("Watchlist")
        body.append(outcome.summary)
        for item in outcome.items:
            body.append(f"{item.ticker} | {item.action} | summary={', '.join(item.source_summary)}")
    elif isinstance(outcome, NoActionOutcome):
        body.append("No Action")
        body.append(outcome.summary)
        body.extend(outcome.reasons)

    body.append(f"Approve: {approval_url}")
    body.append(f"Reject: {rejection_url}")
    return RecommendationEmail(
        subject=f"Investor review for {run_id}",
        body="\n".join(body),
    )


def send_console_email(message: RecommendationEmail) -> RecommendationEmail:
    return message
