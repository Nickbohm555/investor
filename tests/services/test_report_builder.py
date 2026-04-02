from __future__ import annotations

from app.schemas.research import NoActionOutcome, WatchlistOutcome
from app.services.report_builder import build_strategic_insight_report


def test_build_strategic_insight_report_emits_named_watchlist_guidance_fields() -> None:
    outcome = WatchlistOutcome(
        outcome="watchlist",
        summary="Signals are mixed.",
        items=[
            {
                "ticker": "msft",
                "action": "watch",
                "conviction_score": 0.42,
                "supporting_evidence": ["Congress buying increased."],
                "opposing_evidence": ["Insider sales picked up."],
                "risk_notes": ["Need more evidence."],
                "source_summary": ["Mixed Quiver activity."],
                "broker_eligible": False,
            }
        ],
    )

    report = build_strategic_insight_report(
        run_id="run-14",
        outcome=outcome,
        baseline_run_id=None,
        baseline_outcome=None,
    )

    payload = report.research_queue[0].model_dump()

    assert payload["watchlist_reason"] == "Insider sales picked up."
    assert payload["missing_evidence"] == ["Signals are mixed."]
    assert payload["unresolved_questions"] == ["Insider sales picked up."]
    assert payload["next_steps"] == ["Check the next Quiver refresh before approval."]


def test_build_strategic_insight_report_keeps_no_action_research_queue_valid_without_watchlist_items() -> None:
    outcome = NoActionOutcome(
        outcome="no_action",
        summary="Nothing cleared the threshold.",
        reasons=["Signals were stale."],
    )

    report = build_strategic_insight_report(
        run_id="run-14",
        outcome=outcome,
        baseline_run_id=None,
        baseline_outcome=None,
    )

    payload = report.research_queue[0].model_dump()

    assert report.research_queue[0].ticker == "RUN-14"
    assert payload["watchlist_reason"] == "Nothing cleared the threshold."
    assert payload["missing_evidence"] == ["Signals were stale."]
    assert payload["unresolved_questions"] == []
    assert payload["next_steps"] == ["Wait for materially new Quiver evidence before reconsidering."]


def test_build_strategic_insight_report_preserves_prompt_supplied_watchlist_guidance() -> None:
    outcome = WatchlistOutcome(
        outcome="watchlist",
        summary="Signals are mixed.",
        items=[
            {
                "ticker": "msft",
                "action": "watch",
                "conviction_score": 0.42,
                "supporting_evidence": ["Congress buying increased."],
                "opposing_evidence": ["Insider sales picked up."],
                "risk_notes": ["Need more evidence."],
                "source_summary": ["Mixed Quiver activity."],
                "broker_eligible": False,
                "watchlist_reason": "Conflicting conviction after mixed insider and contract signals.",
                "missing_evidence": ["Need two independent supporting filings."],
                "unresolved_questions": ["Did the contract award recur across quarters?"],
                "next_steps": ["Check the next Quiver contracts refresh for repeat awards."],
            }
        ],
    )

    report = build_strategic_insight_report(
        run_id="run-14",
        outcome=outcome,
        baseline_run_id=None,
        baseline_outcome=None,
    )

    payload = report.research_queue[0].model_dump()

    assert payload["watchlist_reason"] == "Conflicting conviction after mixed insider and contract signals."
    assert payload["missing_evidence"] == ["Need two independent supporting filings."]
    assert payload["unresolved_questions"] == ["Did the contract award recur across quarters?"]
    assert payload["next_steps"] == ["Check the next Quiver contracts refresh for repeat awards."]


def test_build_strategic_insight_report_uses_exact_no_action_follow_up_defaults() -> None:
    outcome = NoActionOutcome(
        outcome="no_action",
        summary="Nothing cleared the threshold.",
        reasons=["Signals were stale."],
    )

    report = build_strategic_insight_report(
        run_id="run-14",
        outcome=outcome,
        baseline_run_id=None,
        baseline_outcome=None,
    )

    payload = report.research_queue[0].model_dump()

    assert payload["next_steps"] == ["Wait for materially new Quiver evidence before reconsidering."]
    assert payload["operator_action"] == "Wait for materially new evidence before reconsidering."
