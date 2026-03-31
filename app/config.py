from typing import Literal, Optional

from pydantic import model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "investor"
    app_env: str = "development"
    app_secret: str = "change-me"
    database_url: str = "sqlite+pysqlite:///./investor.db"
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: str = "investor-user"
    smtp_password: str = "change-me"
    smtp_from_email: str = "investor@example.com"
    daily_memo_to_email: str = "operator@example.com"
    external_base_url: str = "https://investor.example.com"
    schedule_cron_expression: str = "30 8 * * 1-5"
    schedule_trigger_url: str = "http://127.0.0.1:8000/runs/trigger/scheduled"
    scheduled_trigger_token: str = "change-me-scheduled-trigger"
    cron_log_path: str = "logs/cron/daily-trigger.log"
    quiver_base_url: str = "https://example.test"
    quiver_api_key: str = "secret"
    broker_mode: Literal["paper", "live"] = "paper"
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_api_key: str = "secret"
    langgraph_checkpointer_url: Optional[str] = None
    approval_token_ttl_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="INVESTOR_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_broker_mode_base_url(self) -> "Settings":
        expected = {
            "paper": "https://paper-api.alpaca.markets",
            "live": "https://api.alpaca.markets",
        }[self.broker_mode]
        if self.alpaca_base_url != expected:
            raise ValueError(
                f"{self.broker_mode} mode requires alpaca_base_url={expected}"
            )
        return self


def get_settings() -> Settings:
    return Settings()
