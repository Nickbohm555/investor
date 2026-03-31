from __future__ import annotations

from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field


class CandidateRecommendation(BaseModel):
    ticker: str
    action: str
    conviction_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    opposing_evidence: List[str] = Field(default_factory=list)
    risk_notes: List[str] = Field(default_factory=list)
    source_summary: List[str] = Field(default_factory=list)
    broker_eligible: bool = True


class CandidateOutcome(BaseModel):
    outcome: Literal["candidates"]
    recommendations: List[CandidateRecommendation]


class WatchlistOutcome(BaseModel):
    outcome: Literal["watchlist"]
    summary: str
    items: List[CandidateRecommendation]


class NoActionOutcome(BaseModel):
    outcome: Literal["no_action"]
    summary: str
    reasons: List[str]


ResearchOutcome = Annotated[
    Union[CandidateOutcome, WatchlistOutcome, NoActionOutcome],
    Field(discriminator="outcome"),
]
