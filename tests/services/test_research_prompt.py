from app.schemas.quiver import SignalRecord, TickerEvidenceBundle
from app.services.research_prompt import build_research_prompt_payload


def test_build_research_prompt_payload_mentions_all_outcomes_and_evidence():
    payload = build_research_prompt_payload(
        run_id="run-123",
        evidence_bundles=[
            TickerEvidenceBundle(
                ticker="NVDA",
                supporting_signals=[
                    SignalRecord(
                        signal_type="congress",
                        ticker="NVDA",
                        direction="positive",
                        magnitude_note="Congress purchase",
                        source_note="Congress buy",
                    )
                ],
                contradictory_signals=[
                    SignalRecord(
                        signal_type="lobbying",
                        ticker="NVDA",
                        direction="mixed",
                        magnitude_note="Lobbying activity",
                        source_note="Lobbying risk",
                    )
                ],
                source_summary=["Congress and lobbying both active"],
            )
        ],
        account_context={"buying_power": "1000", "positions": "AAPL"},
    )

    assert set(payload) == {"system", "user"}
    assert "JSON only" in payload["system"]
    assert "candidates" in payload["system"]
    assert "watchlist" in payload["system"]
    assert "no_action" in payload["system"]
    assert "supporting_evidence" in payload["system"]
    assert "opposing_evidence" in payload["system"]
    assert "risk_notes" in payload["system"]
    assert "source_summary" in payload["system"]
    assert "NVDA" in payload["user"]
    assert "Congress buy" in payload["user"]
    assert "Lobbying risk" in payload["user"]
