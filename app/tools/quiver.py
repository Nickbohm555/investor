from __future__ import annotations

import httpx
from pydantic import TypeAdapter

from app.schemas.quiver import (
    BillSummary,
    CongressionalTrade,
    GovernmentContractAward,
    InsiderTrade,
    LobbyingDisclosure,
)


class QuiverClient:
    def __init__(self, base_url: str, api_key: str, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            transport=transport,
        )

    def _get(self, path: str, params: dict[str, str] | None = None) -> list[dict]:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def get_live_congress_trading(self, ticker: str | None = None) -> list[CongressionalTrade]:
        return TypeAdapter(list[CongressionalTrade]).validate_python(
            self._get("/beta/live/congresstrading", params={"ticker": ticker} if ticker else None)
        )

    def get_live_insider_trading(self, ticker: str | None = None) -> list[InsiderTrade]:
        return TypeAdapter(list[InsiderTrade]).validate_python(
            self._get("/beta/live/insiders", params={"ticker": ticker} if ticker else None)
        )

    def get_live_government_contracts(
        self, ticker: str | None = None
    ) -> list[GovernmentContractAward]:
        return TypeAdapter(list[GovernmentContractAward]).validate_python(
            self._get("/beta/live/govcontracts", params={"ticker": ticker} if ticker else None)
        )

    def get_live_lobbying(self, ticker: str | None = None) -> list[LobbyingDisclosure]:
        return TypeAdapter(list[LobbyingDisclosure]).validate_python(
            self._get("/beta/live/lobbying", params={"ticker": ticker} if ticker else None)
        )

    def get_live_bill_summaries(self, query: str | None = None) -> list[BillSummary]:
        params = {
            "page_size": "10",
            "summary_limit": "5000",
        }
        if query:
            params["query"] = query
        return TypeAdapter(list[BillSummary]).validate_python(
            self._get("/beta/live/billSummaries", params=params)
        )
