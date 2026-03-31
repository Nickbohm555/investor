from app.schemas.workflow import DailyMemoContent, Recommendation, WatchlistItem
from app.services.email import compose_recommendation_email


def test_candidate_email_contains_ranked_candidates_and_signed_links():
    email = compose_recommendation_email(
        run_id="run-123",
        recommendations=DailyMemoContent(
            recommendations=[
                Recommendation(
                    ticker="NVDA",
                    action="buy",
                    conviction_score=0.8,
                    rationale="Congress buy; Signals aligned; Risks: Volatile",
                )
            ],
            watchlist=[],
            no_action_reasons=[],
        ),
        approval_url="https://investor.example.com/approval/approve-token",
        rejection_url="https://investor.example.com/approval/reject-token",
    )

    assert "Ranked Candidates" in email.body
    assert "Approve: https://investor.example.com/approval/approve-token" in email.body
    assert "Reject: https://investor.example.com/approval/reject-token" in email.body
    assert "NVDA | buy | conviction=0.80" in email.body
    assert "Congress buy; Signals aligned; Risks: Volatile" in email.body


def test_watchlist_email_contains_watchlist_heading():
    email = compose_recommendation_email(
        run_id="run-123",
        recommendations=DailyMemoContent(
            recommendations=[],
            watchlist=[
                WatchlistItem(
                    ticker="NVDA",
                    summary="Signals remain mixed after deterministic pruning.",
                )
            ],
            no_action_reasons=[],
        ),
        approval_url="https://investor.example.com/approval/approve-token",
        rejection_url="https://investor.example.com/approval/reject-token",
    )

    assert "Watchlist" in email.body
    assert "NVDA | Signals remain mixed after deterministic pruning." in email.body
    assert "Signals remain mixed after deterministic pruning." in email.body


def test_no_action_email_contains_reason_lines():
    email = compose_recommendation_email(
        run_id="run-123",
        recommendations=DailyMemoContent(
            recommendations=[],
            watchlist=[],
            no_action_reasons=[
                "No qualifying ideas.",
                "No candidates survived deterministic pruning.",
                "Broker eligibility removed the rest.",
            ],
        ),
        approval_url="https://investor.example.com/approval/approve-token",
        rejection_url="https://investor.example.com/approval/reject-token",
    )

    assert "No Action" in email.body
    assert "No qualifying ideas." in email.body
    assert "No candidates survived deterministic pruning." in email.body
    assert "Broker eligibility removed the rest." in email.body
