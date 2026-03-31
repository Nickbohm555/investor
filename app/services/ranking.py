from __future__ import annotations

from typing import List, Optional, Set

from app.schemas.research import (
    CandidateOutcome,
    CandidateRecommendation,
    NoActionOutcome,
    ResearchOutcome,
    WatchlistOutcome,
)
from app.services.broker_eligibility import is_broker_eligible_ticker


def rank_candidates(items: List[CandidateRecommendation]) -> List[CandidateRecommendation]:
    return sorted(
        items,
        key=lambda item: (
            -item.conviction_score,
            -len(item.supporting_evidence),
            len(item.opposing_evidence),
            item.ticker.upper(),
        ),
    )


def dedupe_candidates_by_ticker(items: List[CandidateRecommendation]) -> List[CandidateRecommendation]:
    ranked = rank_candidates(
        [
            item.model_copy(update={"ticker": item.ticker.upper()})
            for item in items
        ]
    )
    deduped: List[CandidateRecommendation] = []
    seen: Set[str] = set()
    for item in ranked:
        if item.ticker in seen:
            continue
        seen.add(item.ticker)
        deduped.append(item)
    return deduped


def finalize_research_outcome(
    outcome: ResearchOutcome,
    minimum_conviction: float = 0.6,
    max_ideas: int = 3,
    allowed_conflict_gap: int = 0,
    watchlist_conviction_ceiling: float = 0.75,
    blocked_tickers: Optional[Set[str]] = None,
) -> ResearchOutcome:
    if not isinstance(outcome, CandidateOutcome):
        return outcome

    survivors = []
    for item in outcome.recommendations:
        normalized = item.model_copy(update={"ticker": item.ticker.upper()})
        if normalized.conviction_score < minimum_conviction:
            continue
        if not is_broker_eligible_ticker(normalized.ticker, blocked_tickers=blocked_tickers):
            continue
        if len(normalized.opposing_evidence) > len(normalized.supporting_evidence) + allowed_conflict_gap:
            continue
        survivors.append(normalized)

    deduped = dedupe_candidates_by_ticker(survivors)
    ranked = rank_candidates(deduped)

    if not ranked:
        return NoActionOutcome(
            outcome="no_action",
            summary="No deterministic candidates remain.",
            reasons=["No candidates survived deterministic pruning."],
        )

    if all(
        item.conviction_score < watchlist_conviction_ceiling
        or len(item.supporting_evidence) <= len(item.opposing_evidence) + 1
        for item in ranked
    ):
        return WatchlistOutcome(
            outcome="watchlist",
            summary="Signals remain mixed after deterministic pruning.",
            items=ranked,
        )

    return CandidateOutcome(
        outcome="candidates",
        recommendations=ranked[:max_ideas],
    )
