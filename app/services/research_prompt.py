from __future__ import annotations

from typing import Dict, List

from app.schemas.quiver import TickerEvidenceBundle


def build_research_prompt_payload(
    run_id: str,
    evidence_bundles: List[TickerEvidenceBundle],
    account_context: Dict[str, str],
) -> Dict[str, str]:
    system = (
        "Return JSON only. "
        "Choose exactly one outcome value from candidates, watchlist, or no_action. "
        "Every recommendation-like item must include supporting_evidence, "
        "opposing_evidence, risk_notes, and source_summary arrays."
    )

    bundle_lines = []
    for bundle in evidence_bundles:
        supporting = ", ".join(signal.source_note for signal in bundle.supporting_signals) or "None"
        contradictory = (
            ", ".join(signal.source_note for signal in bundle.contradictory_signals) or "None"
        )
        summaries = ", ".join(bundle.source_summary) or "None"
        bundle_lines.append(
            f"Ticker: {bundle.ticker}\n"
            f"Supporting signals: {supporting}\n"
            f"Contradictory signals: {contradictory}\n"
            f"Source summaries: {summaries}"
        )

    account_lines = "\n".join(f"{key}: {value}" for key, value in sorted(account_context.items()))
    user = f"Run ID: {run_id}\n{account_lines}\n\n" + "\n\n".join(bundle_lines)

    return {"system": system, "user": user}
