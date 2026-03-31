from app.schemas.quiver import (
    CongressionalTrade,
    GovernmentContractAward,
    InsiderTrade,
    LobbyingDisclosure,
)
from app.services.quiver_normalize import build_ticker_evidence_bundles


def test_build_ticker_evidence_bundles_merges_rows_by_uppercase_ticker():
    bundles = build_ticker_evidence_bundles(
        congress=[CongressionalTrade(Ticker="nvda", Transaction="Purchase")],
        insiders=[InsiderTrade(Ticker="NVDA", Transaction="Buy")],
        gov_contracts=[],
        lobbying=[],
    )

    assert [bundle.ticker for bundle in bundles] == ["NVDA"]
    assert len(bundles[0].supporting_signals) == 2


def test_build_ticker_evidence_bundles_separates_supporting_and_contradictory_trades():
    bundles = build_ticker_evidence_bundles(
        congress=[
            CongressionalTrade(Ticker="NVDA", Transaction="Purchase"),
            CongressionalTrade(Ticker="NVDA", Transaction="Sale"),
        ],
        insiders=[
            InsiderTrade(Ticker="NVDA", Transaction="Buy"),
            InsiderTrade(Ticker="NVDA", Transaction="Sell"),
        ],
        gov_contracts=[],
        lobbying=[],
    )

    bundle = bundles[0]

    assert [signal.direction for signal in bundle.supporting_signals] == ["positive", "positive"]
    assert [signal.direction for signal in bundle.contradictory_signals] == ["negative", "negative"]


def test_build_ticker_evidence_bundles_adds_contextual_contract_and_lobbying_entries():
    bundles = build_ticker_evidence_bundles(
        congress=[],
        insiders=[],
        gov_contracts=[
            GovernmentContractAward(Ticker="PLTR", Agency="DoD", Amount="5000000"),
            GovernmentContractAward(Ticker="MSFT", Agency="DoD", Amount="1000", AmountDescription="Contract termination"),
        ],
        lobbying=[LobbyingDisclosure(Ticker="PLTR", Client="Example Client", Issue="Defense spending")],
    )

    assert [bundle.ticker for bundle in bundles] == ["MSFT", "PLTR"]
    assert bundles[0].contradictory_signals[0].direction == "negative"
    assert bundles[1].supporting_signals == []
    assert bundles[1].contradictory_signals == []
    assert bundles[1].source_summary
