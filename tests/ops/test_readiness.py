from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _explicit_settings(**overrides) -> Settings:
    values = {
        "app_secret": "test-secret",
        "database_url": "sqlite+pysqlite:///:memory:",
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_username": "investor-user",
        "smtp_password": "smtp-password",
        "smtp_from_email": "investor@test.local",
        "daily_memo_to_email": "operator@test.local",
        "external_base_url": "https://investor.test.local",
        "schedule_cron_expression": "30 8 * * 1-5",
        "schedule_trigger_url": "http://127.0.0.1:8000/runs/trigger/scheduled",
        "scheduled_trigger_token": "scheduled-trigger-token",
        "cron_log_path": "logs/cron/daily-trigger.log",
        "quiver_base_url": "https://api.quiverquant.com",
        "quiver_api_key": "quiver-key",
        "broker_mode": "paper",
        "alpaca_base_url": "https://paper-api.alpaca.markets",
        "alpaca_api_key": "alpaca-key",
        "openai_api_key": "openai-key",
        "openai_base_url": "https://api.openai.example/v1",
        "openai_model": "gpt-4.1-mini",
        "approval_token_ttl_seconds": 900,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def test_create_app_rejects_placeholder_operational_values():
    with pytest.raises(ValueError) as excinfo:
        create_app(settings=Settings())

    message = str(excinfo.value)
    assert "INVESTOR_APP_SECRET must not equal change-me" in message
    assert "INVESTOR_SMTP_PASSWORD must not equal change-me" in message
    assert (
        "INVESTOR_SCHEDULED_TRIGGER_TOKEN must not equal change-me-scheduled-trigger"
        in message
    )
    assert "INVESTOR_QUIVER_API_KEY must not equal secret" in message
    assert "INVESTOR_ALPACA_API_KEY must not equal secret" in message
    assert "INVESTOR_OPENAI_API_KEY must not equal replace-with-openai-api-key" in message
    assert "INVESTOR_SMTP_HOST must not equal smtp.example.com" in message
    assert "INVESTOR_EXTERNAL_BASE_URL must not equal https://investor.example.com" in message


def test_create_app_rejects_live_mode_with_paper_alpaca_base_url():
    with pytest.raises(ValueError) as excinfo:
        create_app(
            settings=_explicit_settings(
                broker_mode="live",
                alpaca_base_url="https://paper-api.alpaca.markets",
            )
        )

    assert "INVESTOR_BROKER_MODE=live requires INVESTOR_ALPACA_BASE_URL=https://api.alpaca.markets" in str(
        excinfo.value
    )


def test_create_app_accepts_explicit_non_placeholder_values():
    app = create_app(settings=_explicit_settings())

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
