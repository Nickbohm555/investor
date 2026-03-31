from app.schemas.research import CandidateOutcome, CandidateRecommendation, NoActionOutcome, WatchlistOutcome
from app.services.email import compose_recommendation_email


def test_candidate_email_contains_ranked_candidates_and_signed_links():
    email = compose_recommendation_email(
        run_id="run-123",
        outcome=CandidateOutcome(
            outcome="candidates",
            recommendations=[
                CandidateRecommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.8,
                    supporting_evidence=["Congress buy"],
                    opposing_evidence=[],
                    risk_notes=["Volatile"],
                    source_summary=["Signals aligned"],
                    broker_eligible=True,
                )
            ],
        ),
        approval_url="http://localhost:8000/approval/approve-token",
        rejection_url="http://localhost:8000/approval/reject-token",
    )

    assert "Ranked Candidates" in email.body
    assert "approve-token" in email.body
    assert "reject-token" in email.body
    assert "Congress buy" in email.body


def test_watchlist_email_contains_watchlist_heading():
    email = compose_recommendation_email(
        run_id="run-123",
        outcome=WatchlistOutcome(
            outcome="watchlist",
            summary="Signals remain mixed after deterministic pruning.",
            items=[
                CandidateRecommendation(
                    ticker="NVDA",
                    action="watch",
                    conviction_score=0.7,
                    supporting_evidence=["Congress buy"],
                    opposing_evidence=["Lobbying risk"],
                    risk_notes=["Mixed signals"],
                    source_summary=["Signals diverged"],
                    broker_eligible=True,
                )
            ],
        ),
        approval_url="http://localhost:8000/approval/approve-token",
        rejection_url="http://localhost:8000/approval/reject-token",
    )

    assert "Watchlist" in email.body
    assert "Signals remain mixed after deterministic pruning." in email.body


def test_no_action_email_contains_reason_lines():
    email = compose_recommendation_email(
        run_id="run-123",
        outcome=NoActionOutcome(
            outcome="no_action",
            summary="No qualifying ideas.",
            reasons=["No candidates survived deterministic pruning.", "Broker eligibility removed the rest."],
        ),
        approval_url="http://localhost:8000/approval/approve-token",
        rejection_url="http://localhost:8000/approval/reject-token",
    )

    assert "No Action" in email.body
    assert "No candidates survived deterministic pruning." in email.body
    assert "Broker eligibility removed the rest." in email.body
