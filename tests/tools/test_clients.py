from decimal import Decimal

import httpx

from app.tools.alpaca import AlpacaClient
from app.tools.quiver import QuiverClient


def test_quiver_client_returns_typed_congress_trades():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "secret"
        return httpx.Response(
            200,
            json=[{"Ticker": "NVDA", "Transaction": "Purchase"}],
        )

    transport = httpx.MockTransport(handler)
    client = QuiverClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_congress_trades()

    assert result[0].ticker == "NVDA"


def test_alpaca_client_returns_buying_power():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"buying_power": "1234.56"})

    transport = httpx.MockTransport(handler)
    client = AlpacaClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_buying_power()

    assert result == Decimal("1234.56")
