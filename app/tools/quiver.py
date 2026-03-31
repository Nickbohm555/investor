from __future__ import annotations

from pydantic import BaseModel
import httpx


class CongressTrade(BaseModel):
    ticker: str
    transaction: str


class QuiverClient:
    def __init__(self, base_url: str, api_key: str, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            transport=transport,
        )

    def get_congress_trades(self) -> list[CongressTrade]:
        response = self._client.get("/congresstrading")
        response.raise_for_status()
        data = response.json()
        return [
            CongressTrade(
                ticker=item["Ticker"],
                transaction=item["Transaction"],
            )
            for item in data
        ]
