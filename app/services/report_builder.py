from __future__ import annotations

from app.schemas.reports import (
    DeferredActionItem,
    ImmediateActionItem,
    ResearchNeededItem,
    StrategicInsightReport,
)
from app.schemas.research import CandidateOutcome, CandidateRecommendation, NoActionOutcome, ResearchOutcome, WatchlistOutcome
from app.services.report_compare import compare_candidates


def build_strategic_insight_report(
    *,
    run_id: str,
    outcome: ResearchOutcome,
    baseline_run_id: str | None,
    baseline_outcome: ResearchOutcome | None,
) -> StrategicInsightReport:
    baseline_candidates = _baseline_candidates(baseline_outcome)
    immediate_actions: list[ImmediateActionItem] = []
    deferred_actions: list[DeferredActionItem] = []
    research_queue: list[ResearchNeededItem] = []

    if isinstance(outcome, CandidateOutcome):
        current_candidates = sorted(
            outcome.recommendations,
            key=lambda candidate: candidate.conviction_score,
            reverse=True,
        )
        change_map, dropped_tickers = compare_candidates(
            current=current_candidates,
            previous=baseline_candidates,
        )
        for candidate in current_candidates:
            change_summary = change_map[candidate.ticker.upper()]
            thesis = _build_thesis(candidate)
            if candidate.action == "buy" and candidate.broker_eligible and candidate.conviction_score >= 0.75:
                immediate_actions.append(
                    ImmediateActionItem(
                        ticker=candidate.ticker.upper(),
                        thesis=thesis,
                        change_summary=change_summary,
                        why_now=_build_why_now(candidate),
                        operator_action="Review for approval and paper-order prestage.",
                    )
                )
            elif candidate.action == "buy":
                deferred_actions.append(
                    DeferredActionItem(
                        ticker=candidate.ticker.upper(),
                        thesis=thesis,
                        change_summary=change_summary,
                        defer_reason=_build_defer_reason(candidate),
                        operator_action="Re-check on the next market session.",
                    )
                )
        return _build_report(
            run_id=run_id,
            baseline_run_id=baseline_run_id,
            immediate_actions=immediate_actions,
            deferred_actions=deferred_actions,
            research_queue=research_queue,
            dropped_tickers=dropped_tickers,
        )

    if isinstance(outcome, WatchlistOutcome):
        dropped_tickers = sorted(candidate.ticker.upper() for candidate in baseline_candidates)
        research_queue = [
            ResearchNeededItem(
                ticker=item.ticker.upper(),
                thesis=_build_thesis(item),
                uncertainty=_build_uncertainty(item=item, fallback=outcome.summary),
                follow_up_questions=item.opposing_evidence or [outcome.summary],
                operator_action="Collect more Quiver evidence before approval.",
            )
            for item in outcome.items
        ]
        return _build_report(
            run_id=run_id,
            baseline_run_id=baseline_run_id,
            immediate_actions=immediate_actions,
            deferred_actions=deferred_actions,
            research_queue=research_queue,
            dropped_tickers=dropped_tickers,
        )

    if isinstance(outcome, NoActionOutcome):
        dropped_tickers = sorted(candidate.ticker.upper() for candidate in baseline_candidates)
        research_queue = [
            ResearchNeededItem(
                ticker=run_id.upper(),
                thesis=outcome.summary,
                uncertainty=outcome.summary,
                follow_up_questions=outcome.reasons or [outcome.summary],
                operator_action="Collect more Quiver evidence before approval.",
            )
        ]
        return _build_report(
            run_id=run_id,
            baseline_run_id=baseline_run_id,
            immediate_actions=immediate_actions,
            deferred_actions=deferred_actions,
            research_queue=research_queue,
            dropped_tickers=dropped_tickers,
        )

    raise TypeError(f"Unsupported outcome: {type(outcome)!r}")


def _baseline_candidates(outcome: ResearchOutcome | None) -> list[CandidateRecommendation]:
    if isinstance(outcome, CandidateOutcome):
        return outcome.recommendations
    if isinstance(outcome, WatchlistOutcome):
        return outcome.items
    return []


def _build_report(
    *,
    run_id: str,
    baseline_run_id: str | None,
    immediate_actions: list[ImmediateActionItem],
    deferred_actions: list[DeferredActionItem],
    research_queue: list[ResearchNeededItem],
    dropped_tickers: list[str],
) -> StrategicInsightReport:
    immediate_count = len(immediate_actions)
    defer_count = len(deferred_actions)
    research_count = len(research_queue)
    baseline_label = (
        f"baseline run {baseline_run_id}" if baseline_run_id else "no prior delivered run"
    )
    dropped_label = ", ".join(dropped_tickers) if dropped_tickers else "none"
    return StrategicInsightReport(
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        headline=f"{immediate_count} immediate | {defer_count} defer | {research_count} research",
        summary=f"Compared against {baseline_label}; dropped tickers: {dropped_label}.",
        immediate_actions=immediate_actions,
        deferred_actions=deferred_actions,
        research_queue=research_queue,
        dropped_tickers=dropped_tickers,
    )


def _build_thesis(candidate: CandidateRecommendation) -> str:
    if candidate.source_summary:
        return candidate.source_summary[0]
    if candidate.supporting_evidence:
        return candidate.supporting_evidence[0]
    return candidate.action


def _build_why_now(candidate: CandidateRecommendation) -> str:
    if candidate.supporting_evidence:
        return "; ".join(candidate.supporting_evidence)
    if candidate.source_summary:
        return "; ".join(candidate.source_summary)
    return candidate.action


def _build_defer_reason(candidate: CandidateRecommendation) -> str:
    if not candidate.broker_eligible:
        return "Broker eligibility is false."
    if candidate.conviction_score < 0.75:
        return "Conviction below immediate threshold of 0.75."
    return "Re-check on the next market session."


def _build_uncertainty(*, item: CandidateRecommendation, fallback: str) -> str:
    if item.opposing_evidence:
        return item.opposing_evidence[0]
    return fallback
