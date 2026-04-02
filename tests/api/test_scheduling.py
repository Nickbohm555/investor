from __future__ import annotations

import re

from fastapi.testclient import TestClient


def test_duplicate_scheduled_trigger_returns_duplicate_without_second_primary_run(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": "dry-run-trigger-token"},
    )
    second_response = client.post(
        "/runs/trigger/scheduled",
        headers={"X-Investor-Scheduled-Trigger": "dry-run-trigger-token"},
    )

    first_payload = first_response.json()
    second_payload = second_response.json()

    assert first_response.status_code == 202
    assert first_payload["status"] == "started"
    assert first_payload["duplicate"] is False
    assert re.fullmatch(r"daily:\d{4}-\d{2}-\d{2}", first_payload["schedule_key"])

    assert second_response.status_code == 200
    assert second_payload["status"] == "duplicate"
    assert second_payload["duplicate"] is True
    assert second_payload["schedule_key"] == first_payload["schedule_key"]
    assert second_payload["run_id"] == first_payload["run_id"]
