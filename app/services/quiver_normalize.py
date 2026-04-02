from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict, Iterable, List

from app.schemas.quiver import (
    CongressionalTrade,
    GovernmentContractAward,
    InsiderTrade,
    LobbyingDisclosure,
    SignalRecord,
    TickerEvidenceBundle,
)


def normalize_congressional_trades(rows: Iterable[CongressionalTrade]) -> List[SignalRecord]:
    normalized: List[SignalRecord] = []
    for row in rows:
        direction = "positive" if row.transaction == "Purchase" else "negative" if row.transaction == "Sale" else "mixed"
        normalized.append(
            SignalRecord(
                signal_type="congress",
                ticker=row.ticker.upper(),
                observed_at=_parse_quiver_date(row.filed or row.traded),
                direction=direction,
                magnitude_note=f"Congress transaction: {row.transaction}",
                source_note=f"Congressional trade reported as {row.transaction}.",
            )
        )
    return normalized


def normalize_insider_trades(rows: Iterable[InsiderTrade]) -> List[SignalRecord]:
    normalized: List[SignalRecord] = []
    for row in rows:
        direction = "positive" if row.transaction == "Buy" else "negative" if row.transaction == "Sell" else "mixed"
        normalized.append(
            SignalRecord(
                signal_type="insider",
                ticker=row.ticker.upper(),
                observed_at=_parse_quiver_date(row.file_date or row.date),
                direction=direction,
                magnitude_note=f"Insider transaction: {row.transaction}",
                source_note=f"Insider activity reported as {row.transaction}.",
            )
        )
    return normalized


def normalize_government_contracts(rows: Iterable[GovernmentContractAward]) -> List[SignalRecord]:
    normalized: List[SignalRecord] = []
    for row in rows:
        details = " ".join(part for part in [row.amount_description, row.agency, row.amount] if part)
        detail_text = details.lower()
        direction = "negative" if "cancellation" in detail_text or "termination" in detail_text else "neutral"
        normalized.append(
            SignalRecord(
                signal_type="gov_contract",
                ticker=row.ticker.upper(),
                direction=direction,
                magnitude_note=f"Government contract context: {row.amount or 'unknown amount'}",
                source_note=f"Government contract update from {row.agency or 'unknown agency'}.",
            )
        )
    return normalized


def normalize_lobbying(rows: Iterable[LobbyingDisclosure]) -> List[SignalRecord]:
    normalized: List[SignalRecord] = []
    for row in rows:
        normalized.append(
            SignalRecord(
                signal_type="lobbying",
                ticker=row.ticker.upper(),
                observed_at=_parse_quiver_date(row.date),
                direction="mixed",
                magnitude_note=f"Lobbying issue: {row.issue or 'unspecified issue'}",
                source_note=f"Lobbying disclosure for {row.client or 'unknown client'}.",
            )
        )
    return normalized


def build_ticker_evidence_bundles(
    *,
    congress: Iterable[CongressionalTrade],
    insiders: Iterable[InsiderTrade],
    gov_contracts: Iterable[GovernmentContractAward],
    lobbying: Iterable[LobbyingDisclosure],
) -> List[TickerEvidenceBundle]:
    grouped: DefaultDict[str, TickerEvidenceBundle] = defaultdict(
        lambda: TickerEvidenceBundle(ticker="", supporting_signals=[], contradictory_signals=[], source_summary=[])
    )

    for signal in normalize_congressional_trades(congress):
        bundle = grouped[signal.ticker]
        if not bundle.ticker:
            bundle.ticker = signal.ticker
        _append_signal(bundle, signal)

    for signal in normalize_insider_trades(insiders):
        bundle = grouped[signal.ticker]
        if not bundle.ticker:
            bundle.ticker = signal.ticker
        _append_signal(bundle, signal)

    for signal in normalize_government_contracts(gov_contracts):
        bundle = grouped[signal.ticker]
        if not bundle.ticker:
            bundle.ticker = signal.ticker
        _append_signal(bundle, signal)

    for signal in normalize_lobbying(lobbying):
        bundle = grouped[signal.ticker]
        if not bundle.ticker:
            bundle.ticker = signal.ticker
        _append_signal(bundle, signal)

    bundles = sorted(grouped.values(), key=lambda bundle: bundle.ticker)
    for bundle in bundles:
        _finalize_bundle(bundle)
    return bundles


def _append_signal(bundle: TickerEvidenceBundle, signal: SignalRecord) -> None:
    if signal.direction == "positive":
        bundle.supporting_signals.append(signal)
    elif signal.direction == "negative":
        bundle.contradictory_signals.append(signal)

    bundle.source_summary.append(signal.source_note)


def _parse_quiver_date(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finalize_bundle(bundle: TickerEvidenceBundle) -> None:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    all_signals = bundle.supporting_signals + bundle.contradictory_signals
    dated_signals = [signal for signal in all_signals if signal.observed_at > epoch]
    if dated_signals:
        latest = max(signal.observed_at for signal in dated_signals)
        bundle.latest_signal_at = latest
        bundle.freshness_summary = (
            f"Latest signal: {latest.date().isoformat()}. Dated signals: {len(dated_signals)} of {len(all_signals)}."
        )
    else:
        bundle.latest_signal_at = None
        bundle.freshness_summary = "Latest signal: unknown. Dated signals: 0 of 0."
    bundle.conflict_summary = (
        f"Supporting: {len(bundle.supporting_signals)}. Contradictory: {len(bundle.contradictory_signals)}."
    )
