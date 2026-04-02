from __future__ import annotations

from app.schemas.quiver import CongressionalTrade, InsiderTrade, LobbyingDisclosure
from app.services.quiver_normalize import (
    build_ticker_evidence_bundles,
    normalize_congressional_trades,
    normalize_insider_trades,
    normalize_lobbying,
)


def test_normalizers_capture_observed_dates_from_documented_quiver_rows() -> None:
    congress_signal = normalize_congressional_trades(
        [
            CongressionalTrade(
                Ticker="NVDA",
                Transaction="Purchase",
                Filed="2026-04-02",
                Traded="2026-04-01",
            )
        ]
    )[0]
    insider_signal = normalize_insider_trades(
        [
            InsiderTrade(
                Ticker="NVDA",
                Transaction="Buy",
                Date="2026-03-30",
                fileDate="2026-04-01",
            )
        ]
    )[0]
    lobbying_signal = normalize_lobbying(
        [
            LobbyingDisclosure(
                Ticker="NVDA",
                Client="NVIDIA",
                Issue="Semiconductors",
                Date="2026-03-28",
            )
        ]
    )[0]

    assert congress_signal.observed_at.isoformat() == "2026-04-02T00:00:00+00:00"
    assert insider_signal.observed_at.isoformat() == "2026-04-01T00:00:00+00:00"
    assert lobbying_signal.observed_at.isoformat() == "2026-03-28T00:00:00+00:00"


def test_build_ticker_evidence_bundles_summarizes_freshness_and_conflicts() -> None:
    bundles = build_ticker_evidence_bundles(
        congress=[
            CongressionalTrade(
                Ticker="MSFT",
                Transaction="Purchase",
                Filed="2026-04-02",
                Traded="2026-04-01",
            )
        ],
        insiders=[
            InsiderTrade(
                Ticker="MSFT",
                Transaction="Sell",
                Date="2026-03-31",
                fileDate="2026-04-01",
            )
        ],
        gov_contracts=[],
        lobbying=[],
    )

    assert len(bundles) == 1
    assert bundles[0].freshness_summary == "Latest signal: 2026-04-02. Dated signals: 2 of 2."
    assert bundles[0].conflict_summary == "Supporting: 1. Contradictory: 1."

