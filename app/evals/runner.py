from __future__ import annotations

from collections.abc import Callable, Sequence

from app.evals.scoring import score_execution
from app.evals.types import CaseEvaluation, EvaluationCase, EvaluationReport
from app.schemas.research_agent import ResearchExecutionResult


Runner = Callable[[EvaluationCase], ResearchExecutionResult]


def evaluate_cases(
    cases: Sequence[EvaluationCase],
    *,
    runner: Runner,
    label: str,
) -> EvaluationReport:
    results: list[CaseEvaluation] = []
    total_score = 0.0

    for case in cases:
        execution = runner(case)
        score, metrics = score_execution(case, execution)
        total_score += score
        results.append(
            CaseEvaluation(
                case_id=case.case_id,
                label=label,
                score=score,
                passed=score >= 0.85,
                metrics=metrics,
            )
        )

    return EvaluationReport(label=label, total_score=round(total_score, 4), results=results)


def compare_evaluation_runs(
    cases: Sequence[EvaluationCase],
    *,
    baseline_runner: Runner,
    candidate_runner: Runner,
    baseline_label: str,
    candidate_label: str,
) -> dict[str, object]:
    baseline = evaluate_cases(cases, runner=baseline_runner, label=baseline_label)
    candidate = evaluate_cases(cases, runner=candidate_runner, label=candidate_label)
    baseline_scores = {result.case_id: result.score for result in baseline.results}
    candidate_scores = {result.case_id: result.score for result in candidate.results}
    case_deltas = {
        case_id: round(candidate_scores[case_id] - baseline_scores[case_id], 4)
        for case_id in baseline_scores
    }
    return {
        "baseline": baseline.model_dump(mode="python"),
        "candidate": candidate.model_dump(mode="python"),
        "total_delta": round(candidate.total_score - baseline.total_score, 4),
        "case_deltas": case_deltas,
    }
