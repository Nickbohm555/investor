from __future__ import annotations

from app.schemas.research_agent import AgentTraceStep


def serialize_research_trace(trace: list[AgentTraceStep]) -> list[dict[str, object]]:
    return [
        {
            "step_index": step.step_index,
            "action": step.action,
            "rationale": step.rationale,
            "tool_name": step.tool_name,
            "tool_args": dict(step.tool_args),
            "result_summary": step.result_summary,
        }
        for step in trace
    ]
