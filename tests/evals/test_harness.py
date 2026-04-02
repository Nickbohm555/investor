from __future__ import annotations

from app.evals.cases import DEFAULT_EVALUATION_CASES
from app.evals.runner import compare_evaluation_runs, evaluate_cases
from app.schemas.research import CandidateOutcome, NoActionOutcome, WatchlistOutcome
from app.schemas.research_agent import AgentTraceStep, ResearchExecutionResult


def _result_for_case(case, *, strong: bool) -> ResearchExecutionResult:
    if case.expectation.outcome == "candidates":
        outcome = CandidateOutcome(
            outcome="candidates",
            recommendations=[
                {
                    "ticker": case.expectation.expected_tickers[0],
                    "action": "buy",
                    "conviction_score": 0.88,
                    "supporting_evidence": ["Signals aligned."],
                    "opposing_evidence": [],
                    "risk_notes": ["Needs confirmation."],
                    "source_summary": ["Strong multi-signal alignment."],
                    "broker_eligible": True,
                }
            ],
        )
    elif case.expectation.outcome == "watchlist":
        outcome = WatchlistOutcome(
            outcome="watchlist",
            summary="Signals conflict.",
            items=[
                {
                    "ticker": case.expectation.expected_tickers[0],
                    "action": "watch",
                    "conviction_score": 0.45,
                    "supporting_evidence": ["Congress buying picked up."],
                    "opposing_evidence": ["Insider sales increased."],
                    "risk_notes": ["Need more confirmation."],
                    "source_summary": ["Mixed evidence."],
                    "broker_eligible": False,
                    "watchlist_reason": "Conflicting evidence remains unresolved." if strong else "",
                    "missing_evidence": ["Need a second confirming data point."] if strong else [],
                    "unresolved_questions": ["Did the signal persist across refreshes?"] if strong else [],
                    "next_steps": ["Check the next Quiver refresh."] if strong else [],
                }
            ],
        )
    else:
        outcome = NoActionOutcome(
            outcome="no_action",
            summary="Nothing cleared the threshold.",
            reasons=["Signals were stale."] if strong else [],
        )

    return ResearchExecutionResult(
        outcome=outcome,
        trace=[
            AgentTraceStep(
                step_index=0,
                action="tool_call",
                rationale="Inspecting follow-up evidence before finalizing." if strong else "",
                tool_name="get_live_congress_trading",
                tool_args={"ticker": case.expectation.expected_tickers[0]} if case.expectation.expected_tickers else {},
                result_summary="1 row returned.",
            )
        ],
        stop_reason="final_answer",
        tool_call_count=1,
        investigated_tickers=case.expectation.expected_tickers,
    )


def test_saved_evaluation_cases_cover_all_three_outcome_branches() -> None:
    outcomes = {case.expectation.outcome for case in DEFAULT_EVALUATION_CASES}

    assert outcomes == {"candidates", "watchlist", "no_action"}


def test_evaluate_cases_scores_candidate_watchlist_and_no_action_cases() -> None:
    report = evaluate_cases(
        DEFAULT_EVALUATION_CASES,
        runner=lambda case: _result_for_case(case, strong=True),
        label="strong",
    )

    assert report.label == "strong"
    assert report.total_score == 3.0
    assert {result.case_id for result in report.results} == {case.case_id for case in DEFAULT_EVALUATION_CASES}
    assert all(result.passed for result in report.results)


def test_compare_evaluation_runs_reports_per_case_score_deltas() -> None:
    comparison = compare_evaluation_runs(
        DEFAULT_EVALUATION_CASES,
        baseline_runner=lambda case: _result_for_case(case, strong=False),
        candidate_runner=lambda case: _result_for_case(case, strong=True),
        baseline_label="baseline",
        candidate_label="candidate",
    )

    assert comparison["baseline"]["label"] == "baseline"
    assert comparison["candidate"]["label"] == "candidate"
    assert comparison["total_delta"] > 0
    assert set(comparison["case_deltas"]) == {case.case_id for case in DEFAULT_EVALUATION_CASES}
    assert comparison["case_deltas"]["watchlist-mixed-signals"] > 0
