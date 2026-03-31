from app.schemas.research_agent import AgentTraceStep
from app.services.research_trace import serialize_research_trace


def test_serialize_research_trace_returns_stable_persisted_shape():
    trace = [
        AgentTraceStep(
            step_index=0,
            action="tool_call",
            rationale="Inspect stronger congress signal before synthesizing.",
            tool_name="get_live_congress_trading",
            tool_args={"ticker": "NVDA"},
            result_summary="Congress purchase found.",
        ),
        AgentTraceStep(
            step_index=1,
            action="finalize",
            rationale="Evidence is sufficient to finalize.",
            tool_name=None,
            tool_args={},
            result_summary="Returning candidate outcome.",
        ),
    ]

    assert serialize_research_trace(trace) == [
        {
            "step_index": 0,
            "action": "tool_call",
            "rationale": "Inspect stronger congress signal before synthesizing.",
            "tool_name": "get_live_congress_trading",
            "tool_args": {"ticker": "NVDA"},
            "result_summary": "Congress purchase found.",
        },
        {
            "step_index": 1,
            "action": "finalize",
            "rationale": "Evidence is sufficient to finalize.",
            "tool_name": None,
            "tool_args": {},
            "result_summary": "Returning candidate outcome.",
        },
    ]
