from __future__ import annotations

from app.schemas.research import CandidateRecommendation


def classify_change(*, current: CandidateRecommendation, previous: CandidateRecommendation | None) -> str:
    if previous is None:
        return "new thesis"
    if current.conviction_score > previous.conviction_score:
        return "conviction increased"
    if current.conviction_score < previous.conviction_score:
        return "conviction decreased"
    if current.risk_notes != previous.risk_notes:
        return "risk profile changed"
    return "signal mix unchanged"


def compare_candidates(*, current: list[CandidateRecommendation], previous: list[CandidateRecommendation]) -> tuple[dict[str, str], list[str]]:
    previous_by_ticker = {candidate.ticker.upper(): candidate for candidate in previous}
    current_by_ticker = {candidate.ticker.upper(): candidate for candidate in current}
    change_map = {
        ticker: classify_change(current=candidate, previous=previous_by_ticker.get(ticker))
        for ticker, candidate in current_by_ticker.items()
    }
    dropped_tickers = sorted(
        ticker for ticker in previous_by_ticker.keys() if ticker not in current_by_ticker
    )
    return change_map, dropped_tickers
