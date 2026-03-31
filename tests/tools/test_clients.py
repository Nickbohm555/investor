from decimal import Decimal

import httpx

from app.tools.alpaca import AlpacaClient
from app.tools.quiver import QuiverClient


def test_quiver_client_returns_typed_live_congress_trades():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/beta/live/congresstrading"
        assert request.url.params == httpx.QueryParams()
        assert request.headers["X-API-Key"] == "secret"
        return httpx.Response(
            200,
            json=[{"Ticker": "NVDA", "Transaction": "Purchase", "Representative": "Rep. Example"}],
        )

    transport = httpx.MockTransport(handler)
    client = QuiverClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_live_congress_trading()

    assert result[0].ticker == "NVDA"


def test_quiver_client_returns_typed_live_quiver_datasets_with_ticker_filter():
    expected = [
        (
            "/beta/live/insiders",
            [{"Ticker": "NVDA", "Transaction": "Buy", "InsiderName": "Insider Example"}],
            "get_live_insider_trading",
        ),
        (
            "/beta/live/govcontracts",
            [{"Ticker": "NVDA", "Amount": "1200000", "Agency": "NASA"}],
            "get_live_government_contracts",
        ),
        (
            "/beta/live/lobbying",
            [{"Ticker": "NVDA", "Client": "Example Client", "Issue": "Semiconductors"}],
            "get_live_lobbying",
        ),
    ]

    for path, payload, method_name in expected:
        def handler(request: httpx.Request, *, expected_path: str = path, body: list[dict[str, str]] = payload) -> httpx.Response:
            assert request.url.path == expected_path
            assert request.url.params == httpx.QueryParams({"ticker": "NVDA"})
            assert request.headers["X-API-Key"] == "secret"
            return httpx.Response(200, json=body)

        transport = httpx.MockTransport(handler)
        client = QuiverClient(base_url="https://example.test", api_key="secret", transport=transport)

        result = getattr(client, method_name)(ticker="NVDA")

        assert result[0].ticker == "NVDA"


def test_alpaca_client_returns_buying_power():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"buying_power": "1234.56"})

    transport = httpx.MockTransport(handler)
    client = AlpacaClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_buying_power()

    assert result == Decimal("1234.56")


def test_alpaca_client_returns_account_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/account"
        return httpx.Response(200, json={"buying_power": "1234.56", "trading_blocked": False})

    transport = httpx.MockTransport(handler)
    client = AlpacaClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_account()

    assert result["buying_power"] == "1234.56"
    assert result["trading_blocked"] is False


def test_alpaca_client_returns_asset_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/assets/NVDA"
        return httpx.Response(200, json={"symbol": "NVDA", "tradable": True, "fractionable": True})

    transport = httpx.MockTransport(handler)
    client = AlpacaClient(base_url="https://example.test", api_key="secret", transport=transport)

    result = client.get_asset("NVDA")

    assert result["symbol"] == "NVDA"
    assert result["tradable"] is True
