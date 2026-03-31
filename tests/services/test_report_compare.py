from app.schemas.research import CandidateRecommendation
from app.services.report_compare import classify_change, compare_candidates


def test_classify_change_returns_exact_change_labels():
    previous = CandidateRecommendation(
        ticker="NVDA",
        action="buy",
        conviction_score=0.65,
        supporting_evidence=["Congress buy"],
        opposing_evidence=[],
        risk_notes=["Valuation"],
        source_summary=["Demand remains strong"],
        broker_eligible=True,
    )

    assert (
        classify_change(
            current=CandidateRecommendation(
                ticker="TSLA",
                action="buy",
                conviction_score=0.9,
                supporting_evidence=["New signal"],
                opposing_evidence=[],
                risk_notes=["Volatile"],
                source_summary=["Fresh thesis"],
                broker_eligible=True,
            ),
            previous=None,
        )
        == "new thesis"
    )
    assert (
        classify_change(
            current=CandidateRecommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.8,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Valuation"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            ),
            previous=previous,
        )
        == "conviction increased"
    )
    assert (
        classify_change(
            current=CandidateRecommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.5,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Valuation"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            ),
            previous=previous,
        )
        == "conviction decreased"
    )
    assert (
        classify_change(
            current=CandidateRecommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.65,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Competition rising"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            ),
            previous=previous,
        )
        == "risk profile changed"
    )
    assert (
        classify_change(
            current=CandidateRecommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.65,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Valuation"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            ),
            previous=previous,
        )
        == "signal mix unchanged"
    )


def test_compare_candidates_returns_dropped_tickers_from_baseline_only():
    change_map, dropped = compare_candidates(
        current=[
            CandidateRecommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.8,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Valuation"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            )
        ],
        previous=[
            CandidateRecommendation(
                ticker="nvda",
                action="buy",
                conviction_score=0.7,
                supporting_evidence=["Congress buy"],
                opposing_evidence=[],
                risk_notes=["Valuation"],
                source_summary=["Demand remains strong"],
                broker_eligible=True,
            ),
            CandidateRecommendation(
                ticker="AMD",
                action="buy",
                conviction_score=0.7,
                supporting_evidence=["Insider buy"],
                opposing_evidence=[],
                risk_notes=["Execution"],
                source_summary=["AI demand"],
                broker_eligible=True,
            ),
        ],
    )

    assert change_map["NVDA"] == "conviction increased"
    assert dropped == ["AMD"]
