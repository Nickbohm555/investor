from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ImmediateActionItem(BaseModel):
    bucket: Literal["immediate"] = "immediate"
    ticker: str
    thesis: str = ""
    change_summary: str = ""
    why_now: str = ""
    operator_action: str = ""


class DeferredActionItem(BaseModel):
    bucket: Literal["defer"] = "defer"
    ticker: str
    thesis: str = ""
    change_summary: str = ""
    defer_reason: str = ""
    operator_action: str = ""


class ResearchNeededItem(BaseModel):
    bucket: Literal["research"] = "research"
    ticker: str
    thesis: str = ""
    watchlist_reason: str = ""
    missing_evidence: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    operator_action: str = ""


ReportItem = Annotated[
    Union[ImmediateActionItem, DeferredActionItem, ResearchNeededItem],
    Field(discriminator="bucket"),
]


class StrategicInsightReport(BaseModel):
    run_id: str
    baseline_run_id: Optional[str] = None
    headline: str
    summary: str
    immediate_actions: List[ImmediateActionItem] = Field(default_factory=list)
    deferred_actions: List[DeferredActionItem] = Field(default_factory=list)
    research_queue: List[ResearchNeededItem] = Field(default_factory=list)
    dropped_tickers: List[str] = Field(default_factory=list)
