from pydantic import BaseModel, Field

from app.schemas.research import CandidateOutcome, CandidateRecommendation, ResearchOutcome


class Recommendation(BaseModel):
    ticker: str
    action: str
    conviction_score: float = Field(ge=0.0, le=1.0)
    rationale: str


class ResearchResult(BaseModel):
    recommendations: list[Recommendation]


class RecommendationEmail(BaseModel):
    subject: str
    body: str


ResearchRecommendation = CandidateRecommendation
StructuredResearchResult = CandidateOutcome

__all__ = [
    "CandidateOutcome",
    "CandidateRecommendation",
    "Recommendation",
    "RecommendationEmail",
    "ResearchOutcome",
    "ResearchRecommendation",
    "ResearchResult",
    "StructuredResearchResult",
]
