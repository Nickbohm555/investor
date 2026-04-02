from __future__ import annotations

from app.evals.types import EvaluationCase
from app.schemas.research import CandidateOutcome, NoActionOutcome, WatchlistOutcome
from app.schemas.research_agent import ResearchExecutionResult


OUTCOME_WEIGHT = 0.4
TICKER_WEIGHT = 0.3
GUIDANCE_WEIGHT = 0.15
TRACE_WEIGHT = 0.15


def score_execution(case: EvaluationCase, execution: ResearchExecutionResult) -> tuple[float, dict[str, float]]:
    metrics = {
        "outcome_match": _outcome_score(case, execution),
        "ticker_alignment": _ticker_score(case, execution),
        "guidance_quality": _guidance_score(case, execution),
        "trace_quality": _trace_score(execution),
    }
    score = round(sum(metrics.values()), 4)
    return score, metrics


def _outcome_score(case: EvaluationCase, execution: ResearchExecutionResult) -> float:
    return OUTCOME_WEIGHT if execution.outcome.outcome == case.expectation.outcome else 0.0


def _ticker_score(case: EvaluationCase, execution: ResearchExecutionResult) -> float:
    expected = {ticker.upper() for ticker in case.expectation.expected_tickers}
    actual = set(_actual_tickers(execution))
    return TICKER_WEIGHT if expected.issubset(actual) else 0.0


def _guidance_score(case: EvaluationCase, execution: ResearchExecutionResult) -> float:
    if case.expectation.outcome == "watchlist" and isinstance(execution.outcome, WatchlistOutcome):
        complete = all(
            item.watchlist_reason and item.missing_evidence and item.unresolved_questions and item.next_steps
            for item in execution.outcome.items
        )
        return GUIDANCE_WEIGHT if complete else 0.0
    if case.expectation.outcome == "no_action" and isinstance(execution.outcome, NoActionOutcome):
        return GUIDANCE_WEIGHT if execution.outcome.reasons else 0.0
    if case.expectation.outcome == "candidates" and isinstance(execution.outcome, CandidateOutcome):
        return GUIDANCE_WEIGHT
    return 0.0


def _trace_score(execution: ResearchExecutionResult) -> float:
    has_rationale = any(step.rationale.strip() for step in execution.trace)
    return TRACE_WEIGHT if has_rationale else 0.0


def _actual_tickers(execution: ResearchExecutionResult) -> list[str]:
    if isinstance(execution.outcome, CandidateOutcome):
        return [item.ticker.upper() for item in execution.outcome.recommendations]
    if isinstance(execution.outcome, WatchlistOutcome):
        return [item.ticker.upper() for item in execution.outcome.items]
    return [ticker.upper() for ticker in execution.investigated_tickers]
