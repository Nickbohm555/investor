from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.research import ResearchOutcome


class ResearchAgentBudget(BaseModel):
    max_steps: int = Field(ge=1)
    max_tool_calls: int = Field(ge=0)
    max_seed_tickers: int = Field(ge=1)


class ToolCallRequest(BaseModel):
    tool_name: str
    tool_args: Dict[str, object] = Field(default_factory=dict)


class ToolDecision(BaseModel):
    decision: Literal["tool_call"] = "tool_call"
    rationale: str
    request: ToolCallRequest


class FinalDecision(BaseModel):
    decision: Literal["final"] = "final"
    rationale: str
    outcome: ResearchOutcome


class StopDecision(BaseModel):
    decision: Literal["stop"] = "stop"
    rationale: str
    stop_reason: str


AgentDecision = Union[ToolDecision, FinalDecision, StopDecision]


class AgentTraceStep(BaseModel):
    step_index: int
    action: Literal["tool_call", "finalize", "stop"]
    rationale: str
    tool_name: Optional[str] = None
    tool_args: Dict[str, object] = Field(default_factory=dict)
    result_summary: Optional[str] = None


class ResearchExecutionResult(BaseModel):
    outcome: ResearchOutcome
    trace: List[AgentTraceStep] = Field(default_factory=list)
    stop_reason: str
    tool_call_count: int = Field(ge=0)
    investigated_tickers: List[str] = Field(default_factory=list)
