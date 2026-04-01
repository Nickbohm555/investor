import json

import httpx

from app.tools.alpaca import AlpacaClient


def test_submit_order_posts_client_order_id_and_notional():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"id": "order-123", "status": "accepted"})

    client = AlpacaClient(
        base_url="https://paper-api.alpaca.markets",
        api_key="alpaca-test-key",
        transport=httpx.MockTransport(handler),
    )

    response = client.submit_order(
        symbol="NVDA",
        side="buy",
        order_type="market",
        time_in_force="day",
        client_order_id="run-123-1-paper",
        notional="250.00",
    )

    assert response["status"] == "accepted"
    assert captured["method"] == "POST"
    assert captured["path"] == "/v2/orders"
    assert captured["body"] == {
        "symbol": "NVDA",
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "client_order_id": "run-123-1-paper",
        "notional": "250.00",
    }
