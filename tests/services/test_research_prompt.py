from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.quiver import SignalRecord, TickerEvidenceBundle
from app.services.research_prompt import (
    build_final_research_payload,
    build_quiver_loop_system_prompt,
    build_research_prompt_payload,
)


def _bundle() -> TickerEvidenceBundle:
    return TickerEvidenceBundle(
        ticker="MSFT",
        supporting_signals=[
            SignalRecord(
                signal_type="congress",
                ticker="MSFT",
                observed_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
                direction="positive",
                magnitude_note="Representative bought shares.",
                source_note="Congress buy",
            )
        ],
        contradictory_signals=[],
        source_summary=["Positive congressional activity."],
    )


def test_build_final_research_payload_requires_watchlist_guidance_keys() -> None:
    payload = build_final_research_payload(
        run_id="run-14",
        evidence_bundles=[_bundle()],
        account_context={"account_size": "paper"},
        trace_summary="No additional tool calls.",
    )

    assert "Every watchlist item must include watchlist_reason, missing_evidence, unresolved_questions, and next_steps." in payload["system"]
    assert "candidates, watchlist, or no_action." in payload["system"]


def test_build_research_prompt_payload_keeps_json_only_watchlist_contract() -> None:
    payload = build_research_prompt_payload(
        run_id="run-14",
        evidence_bundles=[_bundle()],
        account_context={"account_size": "paper"},
    )

    assert "Return JSON only." in payload["system"]
    assert "Every watchlist item must include watchlist_reason, missing_evidence, unresolved_questions, and next_steps." in payload["system"]
    assert "candidates, watchlist, or no_action." in payload["system"]


def test_build_quiver_loop_system_prompt_mentions_bill_summaries_and_rationale_instruction() -> None:
    system_prompt = build_quiver_loop_system_prompt(max_steps=4, max_tool_calls=3)

    assert "get_live_bill_summaries" in system_prompt
    assert "explain why each follow-up tool call is needed before using it" in system_prompt


def test_build_final_research_payload_requires_staleness_conflict_and_confirmation_language() -> None:
    payload = build_final_research_payload(
        run_id="run-16",
        evidence_bundles=[_bundle()],
        account_context={"account_size": "paper"},
        trace_summary="One follow-up tool call executed.",
    )

    assert (
        "For watchlist and no_action outputs, explicitly call out stale evidence, conflicting signals, and missing confirmation before approval."
        in payload["system"]
    )
