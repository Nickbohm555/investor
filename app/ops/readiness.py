from __future__ import annotations

from app.config import Settings
from app.services.research_llm import provider_capability_missing

PLACEHOLDER_ASSIGNMENTS = [
    "INVESTOR_APP_SECRET=change-me",
    "INVESTOR_DATABASE_URL=sqlite+pysqlite:///./investor.db",
    "INVESTOR_SMTP_HOST=smtp.example.com",
    "INVESTOR_SMTP_PASSWORD=change-me",
    "INVESTOR_SMTP_FROM_EMAIL=investor@example.com",
    "INVESTOR_DAILY_MEMO_TO_EMAIL=operator@example.com",
    "INVESTOR_EXTERNAL_BASE_URL=https://investor.example.com",
    "INVESTOR_SCHEDULED_TRIGGER_TOKEN=change-me-scheduled-trigger",
    "INVESTOR_QUIVER_BASE_URL=https://example.test",
    "INVESTOR_QUIVER_API_KEY=secret",
    "INVESTOR_ALPACA_API_KEY=secret",
    "INVESTOR_OPENAI_API_KEY=replace-with-openai-api-key",
]


class OperationalReadinessError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def collect_readiness_errors(settings: Settings) -> list[str]:
    errors: list[str] = []
    for assignment in PLACEHOLDER_ASSIGNMENTS:
        env_name, placeholder = assignment.split("=", 1)
        field_name = env_name.removeprefix("INVESTOR_").lower()
        if getattr(settings, field_name) == placeholder:
            errors.append(f"{env_name} must not equal {placeholder}")

    expected_base_url = {
        "paper": "https://paper-api.alpaca.markets",
        "live": "https://api.alpaca.markets",
    }[settings.broker_mode]
    if settings.alpaca_base_url != expected_base_url:
        errors.append(
            f"INVESTOR_BROKER_MODE={settings.broker_mode} requires "
            f"INVESTOR_ALPACA_BASE_URL={expected_base_url}"
        )

    loop_budget_fields = [
        ("INVESTOR_RESEARCH_AGENT_MAX_STEPS", settings.research_agent_max_steps),
        ("INVESTOR_RESEARCH_AGENT_MAX_TOOL_CALLS", settings.research_agent_max_tool_calls),
        ("INVESTOR_RESEARCH_AGENT_MAX_SEED_TICKERS", settings.research_agent_max_seed_tickers),
    ]
    for env_name, value in loop_budget_fields:
        if value < 1:
            errors.append(f"{env_name} must be greater than 0")

    provider_error = provider_capability_missing(settings.openai_base_url)
    if provider_error is not None:
        errors.append(provider_error)

    return errors


def assert_startup_readiness(settings: Settings, session_factory) -> None:
    errors = collect_readiness_errors(settings)

    bind = getattr(session_factory, "kw", {}).get("bind")
    if bind is None:
        errors.append("Session factory is missing a bound engine")
    else:
        try:
            with bind.connect():
                pass
        except Exception as exc:
            errors.append(f"Database connection failed for {settings.database_url}: {exc}")

    if errors:
        raise OperationalReadinessError(errors)
