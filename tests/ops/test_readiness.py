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
        "research_agent_max_steps": 4,
        "research_agent_max_tool_calls": 3,
        "research_agent_max_seed_tickers": 2,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def _placeholder_settings() -> Settings:
    return Settings.model_validate(
        {
            "app_secret": "change-me",
            "database_url": "sqlite+pysqlite:///./investor.db",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "investor-user",
            "smtp_password": "change-me",
            "smtp_from_email": "investor@example.com",
            "daily_memo_to_email": "operator@example.com",
            "external_base_url": "https://investor.example.com",
            "schedule_cron_expression": "30 8 * * 1-5",
            "schedule_trigger_url": "http://127.0.0.1:8000/runs/trigger/scheduled",
            "scheduled_trigger_token": "change-me-scheduled-trigger",
            "cron_log_path": "logs/cron/daily-trigger.log",
            "quiver_base_url": "https://example.test",
            "quiver_api_key": "secret",
            "broker_mode": "paper",
            "alpaca_base_url": "https://paper-api.alpaca.markets",
            "alpaca_api_key": "secret",
            "openai_api_key": "replace-with-openai-api-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4.1-mini",
            "approval_token_ttl_seconds": 900,
            "research_agent_max_steps": 4,
            "research_agent_max_tool_calls": 3,
            "research_agent_max_seed_tickers": 2,
        }
    )


def test_settings_expose_positive_loop_agent_controls():
    settings = _explicit_settings(
        research_agent_max_steps=5,
        research_agent_max_tool_calls=4,
        research_agent_max_seed_tickers=3,
    )

    assert settings.research_agent_max_steps == 5
    assert settings.research_agent_max_tool_calls == 4
    assert settings.research_agent_max_seed_tickers == 3


def test_create_app_rejects_placeholder_operational_values():
    with pytest.raises(ValueError) as excinfo:
        create_app(settings=_placeholder_settings())

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


def test_create_app_rejects_non_positive_loop_budgets():
    with pytest.raises(ValueError) as excinfo:
        create_app(
            settings=_explicit_settings(
                research_agent_max_steps=0,
                research_agent_max_tool_calls=-1,
                research_agent_max_seed_tickers=0,
            )
        )

    message = str(excinfo.value)
    assert "INVESTOR_RESEARCH_AGENT_MAX_STEPS must be greater than 0" in message
    assert "INVESTOR_RESEARCH_AGENT_MAX_TOOL_CALLS must be greater than 0" in message
    assert "INVESTOR_RESEARCH_AGENT_MAX_SEED_TICKERS must be greater than 0" in message


def test_create_app_rejects_provider_without_required_tool_calling_contract():
    with pytest.raises(ValueError) as excinfo:
        create_app(
            settings=_explicit_settings(
                openai_base_url="https://api.openai.example/compat",
            )
        )

    assert "does not expose the required /v1 OpenAI-compatible tool-calling surface" in str(
        excinfo.value
    )


def test_create_app_accepts_explicit_non_placeholder_values():
    app = create_app(settings=_explicit_settings())

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert app.state.research_node._budget.max_steps == 4
    assert app.state.research_node._budget.max_tool_calls == 3
    assert app.state.research_node._budget.max_seed_tickers == 2
