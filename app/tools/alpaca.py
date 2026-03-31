from __future__ import annotations

from decimal import Decimal

import httpx


class AlpacaClient:
    def __init__(self, base_url: str, api_key: str, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    def get_buying_power(self) -> Decimal:
        response = self._client.get("/v2/account")
        response.raise_for_status()
        return Decimal(response.json()["buying_power"])

    def get_account(self) -> dict:
        response = self._client.get("/v2/account")
        response.raise_for_status()
        return response.json()

    def get_asset(self, symbol: str) -> dict:
        response = self._client.get(f"/v2/assets/{symbol}")
        response.raise_for_status()
        return response.json()
