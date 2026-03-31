from __future__ import annotations

import httpx
from pydantic import TypeAdapter

from app.schemas.quiver import (
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

    def _get(self, path: str, ticker: str | None = None) -> list[dict]:
        params = {"ticker": ticker} if ticker else None
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def get_live_congress_trading(self, ticker: str | None = None) -> list[CongressionalTrade]:
        return TypeAdapter(list[CongressionalTrade]).validate_python(
            self._get("/beta/live/congresstrading", ticker=ticker)
        )

    def get_live_insider_trading(self, ticker: str | None = None) -> list[InsiderTrade]:
        return TypeAdapter(list[InsiderTrade]).validate_python(
            self._get("/beta/live/insiders", ticker=ticker)
        )

    def get_live_government_contracts(
        self, ticker: str | None = None
    ) -> list[GovernmentContractAward]:
        return TypeAdapter(list[GovernmentContractAward]).validate_python(
            self._get("/beta/live/govcontracts", ticker=ticker)
        )

    def get_live_lobbying(self, ticker: str | None = None) -> list[LobbyingDisclosure]:
        return TypeAdapter(list[LobbyingDisclosure]).validate_python(
            self._get("/beta/live/lobbying", ticker=ticker)
        )
