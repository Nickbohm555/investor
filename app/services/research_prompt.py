from __future__ import annotations

from typing import Dict, List

from app.schemas.quiver import TickerEvidenceBundle


def build_quiver_loop_system_prompt(*, max_steps: int, max_tool_calls: int) -> str:
    return (
        "You are the investor research loop. Operate as a serial tool user and issue "
        "one tool call at a time. Available tools: get_live_congress_trading, "
        "get_live_insider_trading, get_live_government_contracts, get_live_lobbying, "
        "get_live_bill_summaries. explain why each follow-up tool call is needed before using it. "
        f"Max steps: {max_steps}. Max tool calls: {max_tool_calls}. "
        "Stop when evidence is sufficient, when no ticker remains worth investigating, "
        "or when a budget limit is reached."
    )


def build_seed_research_brief(
    *,
    run_id: str,
    evidence_bundles: List[TickerEvidenceBundle],
    account_context: Dict[str, str],
    max_seed_tickers: int,
) -> str:
    sorted_bundles = sorted(
        evidence_bundles,
        key=lambda bundle: (
            -len(bundle.supporting_signals),
            len(bundle.contradictory_signals),
            bundle.ticker,
        ),
    )[:max_seed_tickers]
    account_lines = "\n".join(f"{key}: {value}" for key, value in sorted(account_context.items()))
    bundle_lines = []
    for bundle in sorted_bundles:
        supporting = ", ".join(signal.source_note for signal in bundle.supporting_signals) or "None"
        contradictory = (
            ", ".join(signal.source_note for signal in bundle.contradictory_signals) or "None"
        )
        summaries = ", ".join(bundle.source_summary) or "None"
        bundle_lines.append(
            f"Ticker: {bundle.ticker}\n"
            f"Supporting signals: {supporting}\n"
            f"Contradictory signals: {contradictory}\n"
            f"Source summaries: {summaries}\n"
            f"Freshness summary: {bundle.freshness_summary or 'Unknown'}\n"
            f"Conflict summary: {bundle.conflict_summary or 'Unknown'}"
        )

    return f"Run ID: {run_id}\n{account_lines}\n\n" + "\n\n".join(bundle_lines)


def build_final_research_payload(
    *,
    run_id: str,
    evidence_bundles: List[TickerEvidenceBundle],
    account_context: Dict[str, str],
    trace_summary: str,
) -> Dict[str, str]:
    payload = build_seed_research_brief(
        run_id=run_id,
        evidence_bundles=evidence_bundles,
        account_context=account_context,
        max_seed_tickers=len(evidence_bundles),
    )
    return {
        "system": (
            "Return JSON only. Choose exactly one outcome value from candidates, watchlist, or no_action. "
            "Every recommendation-like item must include supporting_evidence, opposing_evidence, risk_notes, "
            "and source_summary arrays. Every watchlist item must include watchlist_reason, missing_evidence, "
            "unresolved_questions, and next_steps. For watchlist and no_action outputs, explicitly call out "
            "stale evidence, conflicting signals, and missing confirmation before approval."
        ),
        "user": f"{payload}\n\nResearch trace summary:\n{trace_summary}",
    }


def build_research_prompt_payload(
    run_id: str,
    evidence_bundles: List[TickerEvidenceBundle],
    account_context: Dict[str, str],
) -> Dict[str, str]:
    return build_final_research_payload(
        run_id=run_id,
        evidence_bundles=evidence_bundles,
        account_context=account_context,
        trace_summary="No follow-up tool calls executed.",
    )
