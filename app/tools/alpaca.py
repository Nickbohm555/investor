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

    def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        time_in_force: str,
        client_order_id: str,
        notional: str | None = None,
        qty: str | None = None,
    ) -> dict:
        payload = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
            "client_order_id": client_order_id,
        }
        if notional is not None:
            payload["notional"] = notional
        if qty is not None:
            payload["qty"] = qty

        response = self._client.post("/v2/orders", json=payload)
        response.raise_for_status()
        return response.json()
