from app.schemas.workflow import Recommendation
from app.services.risk import filter_recommendations


def test_filter_recommendations_removes_low_conviction_and_duplicates():
    recommendations = [
        Recommendation(ticker="NVDA", conviction_score=0.8, action="buy", rationale="signal"),
        Recommendation(ticker="NVDA", conviction_score=0.8, action="buy", rationale="signal"),
        Recommendation(ticker="TSLA", conviction_score=0.3, action="buy", rationale="weak"),
    ]

    filtered = filter_recommendations(recommendations, minimum_conviction=0.6, max_ideas=3)

    assert [item.ticker for item in filtered] == ["NVDA"]
