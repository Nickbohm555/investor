from app.schemas.quiver import SignalRecord, TickerEvidenceBundle
from app.services.research_prompt import (
    build_final_research_payload,
    build_quiver_loop_system_prompt,
    build_research_prompt_payload,
    build_seed_research_brief,
)


def _bundle(
    ticker: str,
    *,
    supporting: list[str],
    contradictory: list[str],
    summaries: list[str],
) -> TickerEvidenceBundle:
    return TickerEvidenceBundle(
        ticker=ticker,
        supporting_signals=[
            SignalRecord(
                signal_type="congress",
                ticker=ticker,
                direction="positive",
                magnitude_note=note,
                source_note=note,
            )
            for note in supporting
        ],
        contradictory_signals=[
            SignalRecord(
                signal_type="lobbying",
                ticker=ticker,
                direction="mixed",
                magnitude_note=note,
                source_note=note,
            )
            for note in contradictory
        ],
        source_summary=summaries,
    )


def test_build_quiver_loop_system_prompt_defines_serial_tool_loop_and_stop_conditions():
    prompt = build_quiver_loop_system_prompt(max_steps=4, max_tool_calls=3)

    assert "serial" in prompt.lower()
    assert "one tool call at a time" in prompt.lower()
    assert "get_live_congress_trading" in prompt
    assert "get_live_insider_trading" in prompt
    assert "get_live_government_contracts" in prompt
    assert "get_live_lobbying" in prompt
    assert "max steps: 4" in prompt.lower()
    assert "max tool calls: 3" in prompt.lower()
    assert "stop" in prompt.lower()
    assert "budget" in prompt.lower()


def test_build_seed_research_brief_prioritizes_strongest_bundles_and_account_context():
    brief = build_seed_research_brief(
        run_id="run-123",
        evidence_bundles=[
            _bundle(
                "NVDA",
                supporting=["Congress buy", "Insider buy"],
                contradictory=["Lobbying risk"],
                summaries=["Congress and insider activity aligned"],
            ),
            _bundle(
                "MSFT",
                supporting=["Contract win"],
                contradictory=[],
                summaries=["Government contract momentum"],
            ),
            _bundle(
                "AAPL",
                supporting=[],
                contradictory=["Lobbying pressure", "Insider sale"],
                summaries=["Mixed signals"],
            ),
        ],
        account_context={"buying_power": "1000", "positions": "AAPL"},
        max_seed_tickers=2,
    )

    assert "Run ID: run-123" in brief
    assert "buying_power: 1000" in brief
    assert "positions: AAPL" in brief
    assert "NVDA" in brief
    assert "MSFT" in brief
    assert "Ticker: AAPL" not in brief
    assert "Congress buy" in brief
    assert "Government contract momentum" in brief


def test_build_final_research_payload_preserves_research_outcome_contract():
    payload = build_final_research_payload(
        run_id="run-123",
        evidence_bundles=[
            _bundle(
                "NVDA",
                supporting=["Congress buy"],
                contradictory=["Lobbying risk"],
                summaries=["Congress and lobbying both active"],
            )
        ],
        account_context={"buying_power": "1000", "positions": "AAPL"},
        trace_summary="Step 1: inspected NVDA congress activity.",
    )

    assert set(payload) == {"system", "user"}
    assert "json only" in payload["system"].lower()
    assert "candidates" in payload["system"]
    assert "watchlist" in payload["system"]
    assert "no_action" in payload["system"]
    assert "supporting_evidence" in payload["system"]
    assert "opposing_evidence" in payload["system"]
    assert "risk_notes" in payload["system"]
    assert "source_summary" in payload["system"]
    assert "Step 1: inspected NVDA congress activity." in payload["user"]
    assert "NVDA" in payload["user"]


def test_build_research_prompt_payload_wraps_final_payload_for_backward_compatibility():
    payload = build_research_prompt_payload(
        run_id="run-123",
        evidence_bundles=[
            _bundle(
                "NVDA",
                supporting=["Congress buy"],
                contradictory=["Lobbying risk"],
                summaries=["Congress and lobbying both active"],
            )
        ],
        account_context={"buying_power": "1000", "positions": "AAPL"},
    )

    assert set(payload) == {"system", "user"}
    assert "json only" in payload["system"].lower()
    assert "NVDA" in payload["user"]
