from app.schemas.research import CandidateOutcome, CandidateRecommendation
from app.services.ranking import (
    dedupe_candidates_by_ticker,
    finalize_research_outcome,
    rank_candidates,
)


def _candidate(
    ticker: str,
    conviction_score: float,
    *,
    supporting: list[str],
    opposing: list[str],
    broker_eligible: bool = True,
) -> CandidateRecommendation:
    return CandidateRecommendation(
        ticker=ticker,
        action="buy",
        conviction_score=conviction_score,
        supporting_evidence=supporting,
        opposing_evidence=opposing,
        risk_notes=["Volatile"],
        source_summary=["Signals gathered"],
        broker_eligible=broker_eligible,
    )


def test_dedupe_candidates_by_ticker_keeps_highest_ranked_version():
    deduped = dedupe_candidates_by_ticker(
        [
            _candidate("nvda", 0.8, supporting=["A"], opposing=[]),
            _candidate("NVDA", 0.9, supporting=["A", "B"], opposing=[]),
        ]
    )

    assert [item.ticker for item in deduped] == ["NVDA"]
    assert deduped[0].conviction_score == 0.9


def test_rank_candidates_sorts_deterministically():
    ranked = rank_candidates(
        [
            _candidate("MSFT", 0.8, supporting=["A"], opposing=[]),
            _candidate("NVDA", 0.9, supporting=["A"], opposing=[]),
            _candidate("AAPL", 0.9, supporting=["A", "B"], opposing=[]),
            _candidate("AMD", 0.9, supporting=["A", "B"], opposing=["risk"]),
        ]
    )

    assert [item.ticker for item in ranked] == ["AAPL", "AMD", "NVDA", "MSFT"]


def test_finalize_research_outcome_returns_watchlist_for_weak_survivors():
    outcome = finalize_research_outcome(
        CandidateOutcome(
            outcome="candidates",
            recommendations=[
                _candidate("NVDA", 0.74, supporting=["A", "B"], opposing=["risk"]),
                _candidate("MSFT", 0.7, supporting=["A"], opposing=[]),
            ],
        ),
        max_ideas=3,
    )

    assert outcome.outcome == "watchlist"
    assert outcome.summary == "Signals remain mixed after deterministic pruning."


def test_finalize_research_outcome_returns_no_action_when_all_candidates_drop():
    outcome = finalize_research_outcome(
        CandidateOutcome(
            outcome="candidates",
            recommendations=[
                _candidate("NVDA", 0.59, supporting=["A"], opposing=[]),
                _candidate("MSFT", 0.8, supporting=["A"], opposing=["risk", "risk-2"]),
            ],
        )
    )

    assert outcome.outcome == "no_action"
    assert "No candidates survived deterministic pruning." in outcome.reasons


def test_finalize_research_outcome_ignores_llm_broker_flag_and_uses_blocked_tickers():
    outcome = finalize_research_outcome(
        CandidateOutcome(
            outcome="candidates",
            recommendations=[
                _candidate("NVDA", 0.81, supporting=["A", "B"], opposing=[], broker_eligible=False),
                _candidate("MSFT", 0.8, supporting=["A", "B"], opposing=[]),
                _candidate("TSLA", 0.95, supporting=["A", "B"], opposing=[]),
            ],
        ),
        blocked_tickers={"TSLA"},
    )

    assert outcome.outcome == "candidates"
    assert [item.ticker for item in outcome.recommendations] == ["NVDA", "MSFT"]
