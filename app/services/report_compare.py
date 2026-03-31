from __future__ import annotations

from app.schemas.research import CandidateRecommendation


def classify_change(
    *, current: CandidateRecommendation, previous: CandidateRecommendation | None
) -> str:
    raise NotImplementedError


def compare_candidates(
    *,
    current: list[CandidateRecommendation],
    previous: list[CandidateRecommendation],
) -> tuple[dict[str, str], list[str]]:
    raise NotImplementedError
