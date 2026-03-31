from pydantic import BaseModel, Field


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
