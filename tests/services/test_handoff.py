from app.schemas.workflow import Recommendation
from app.services.handoff import build_alpaca_handoff


def test_build_alpaca_handoff_returns_structured_payload():
    handoff = build_alpaca_handoff(
        run_id="run-123",
        recommendations=[
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.8,
                rationale="signal",
            )
        ],
    )

    assert handoff["run_id"] == "run-123"
    assert handoff["recommendations"][0]["ticker"] == "NVDA"
