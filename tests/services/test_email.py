from app.schemas.workflow import Recommendation
from app.services.email import compose_recommendation_email


def test_console_email_contains_signed_review_links():
    email = compose_recommendation_email(
        run_id="run-123",
        recommendations=[
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.8,
                rationale="signal",
            )
        ],
        approval_url="http://localhost:8000/approval/approve-token",
        rejection_url="http://localhost:8000/approval/reject-token",
    )

    assert "approve-token" in email.body
    assert "reject-token" in email.body
