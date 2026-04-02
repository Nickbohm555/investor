from pydantic import BaseModel, Field

from app.schemas.research import (
    CandidateOutcome,
    CandidateRecommendation,
    ResearchOutcome,
    WatchlistCandidate,
)
from app.schemas.reports import StrategicInsightReport


class Recommendation(BaseModel):
    ticker: str
    action: str
    conviction_score: float = Field(ge=0.0, le=1.0)
    rationale: str


class WatchlistItem(BaseModel):
    ticker: str
    summary: str


class DailyMemoContent(BaseModel):
    recommendations: list[Recommendation] = Field(default_factory=list)
    watchlist: list[WatchlistItem] = Field(default_factory=list)
    no_action_reasons: list[str] = Field(default_factory=list)


class ResearchResult(BaseModel):
    recommendations: list[Recommendation]


class RecommendationEmail(BaseModel):
    subject: str
    body: str
    html_body: str


ResearchRecommendation = CandidateRecommendation
StructuredResearchResult = CandidateOutcome

__all__ = [
    "CandidateOutcome",
    "CandidateRecommendation",
    "DailyMemoContent",
    "Recommendation",
    "RecommendationEmail",
    "ResearchOutcome",
    "ResearchRecommendation",
    "ResearchResult",
    "StrategicInsightReport",
    "StructuredResearchResult",
    "WatchlistCandidate",
    "WatchlistItem",
]
