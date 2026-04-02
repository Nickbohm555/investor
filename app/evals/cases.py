from __future__ import annotations

from datetime import datetime, timezone

from app.evals.types import EvaluationCase, EvaluationExpectation
from app.schemas.quiver import SignalRecord, TickerEvidenceBundle


def _signal(ticker: str, signal_type: str, direction: str, note: str) -> SignalRecord:
    return SignalRecord(
        signal_type=signal_type,  # type: ignore[arg-type]
        ticker=ticker,
        observed_at=datetime(2026, 4, 2, tzinfo=timezone.utc),
        direction=direction,  # type: ignore[arg-type]
        magnitude_note=note,
        source_note=note,
    )


DEFAULT_EVALUATION_CASES = [
    EvaluationCase(
        case_id="candidate-high-conviction",
        description="Aligned positive signals should surface a candidate recommendation.",
        run_id="eval-candidate",
        evidence_bundles=[
            TickerEvidenceBundle(
                ticker="NVDA",
                supporting_signals=[
                    _signal("NVDA", "congress", "positive", "Congressional purchase increased."),
                    _signal("NVDA", "insider", "positive", "Insider buying aligned."),
                ],
                contradictory_signals=[],
                source_summary=["Strong multi-signal alignment."],
            )
        ],
        account_context={"account_size": "paper"},
        expectation=EvaluationExpectation(
            outcome="candidates",
            expected_tickers=["NVDA"],
        ),
    ),
    EvaluationCase(
        case_id="watchlist-mixed-signals",
        description="Mixed evidence should stay on the watchlist with explicit follow-up guidance.",
        run_id="eval-watchlist",
        evidence_bundles=[
            TickerEvidenceBundle(
                ticker="MSFT",
                supporting_signals=[
                    _signal("MSFT", "congress", "positive", "Congressional buying picked up."),
                ],
                contradictory_signals=[
                    _signal("MSFT", "insider", "negative", "Insider selling increased."),
                ],
                source_summary=["Mixed evidence."],
            )
        ],
        account_context={"account_size": "paper"},
        expectation=EvaluationExpectation(
            outcome="watchlist",
            expected_tickers=["MSFT"],
        ),
    ),
    EvaluationCase(
        case_id="no-action-stale-evidence",
        description="Stale or weak evidence should produce a no-action result.",
        run_id="eval-no-action",
        evidence_bundles=[
            TickerEvidenceBundle(
                ticker="SHOP",
                supporting_signals=[],
                contradictory_signals=[],
                source_summary=["Signals are stale and inconclusive."],
            )
        ],
        account_context={"account_size": "paper"},
        expectation=EvaluationExpectation(
            outcome="no_action",
            expected_tickers=["SHOP"],
        ),
    ),
]
