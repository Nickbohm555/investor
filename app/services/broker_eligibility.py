from __future__ import annotations

from typing import Optional, Set


def is_broker_eligible_ticker(
    ticker: str,
    blocked_tickers: Optional[Set[str]] = None,
) -> bool:
    normalized = ticker.upper()
    blocked = {item.upper() for item in (blocked_tickers or set())}
    return normalized not in blocked
