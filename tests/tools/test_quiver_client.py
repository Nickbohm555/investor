from __future__ import annotations

import httpx

from app.tools.quiver import QuiverClient


def test_quiver_client_returns_typed_bill_summaries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://api.quiver.test/beta/live/billSummaries?page_size=10&summary_limit=5000&query=energy"
        )
        assert request.headers["X-API-Key"] == "secret"
        return httpx.Response(
            200,
            json=[
                {
                    "Title": "American Energy Storage Act",
                    "Congress": "119",
                    "Number": "H.R.123",
                    "originChamber": "House",
                    "currentChamber": "Senate",
                    "billType": "hr",
                    "Summary": "Supports grid-scale storage projects.",
                    "URL": "https://example.test/bills/123",
                    "lastAction": "Placed on Senate calendar",
                    "lastActionDate": "2026-04-01",
                }
            ],
        )

    client = QuiverClient(
        base_url="https://api.quiver.test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )

    rows = client.get_live_bill_summaries(query="energy")

    assert len(rows) == 1
    assert rows[0].title == "American Energy Storage Act"
    assert rows[0].last_action_date == "2026-04-01"
