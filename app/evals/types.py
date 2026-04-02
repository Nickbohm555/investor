from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field

from app.schemas.quiver import TickerEvidenceBundle


class EvaluationExpectation(BaseModel):
    outcome: Literal["candidates", "watchlist", "no_action"]
    expected_tickers: List[str] = Field(default_factory=list)


class EvaluationCase(BaseModel):
    case_id: str
    description: str
    run_id: str
    evidence_bundles: List[TickerEvidenceBundle] = Field(default_factory=list)
    account_context: Dict[str, str] = Field(default_factory=dict)
    expectation: EvaluationExpectation


class CaseEvaluation(BaseModel):
    case_id: str
    label: str
    score: float
    passed: bool
    metrics: Dict[str, float] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    label: str
    total_score: float
    results: List[CaseEvaluation] = Field(default_factory=list)
