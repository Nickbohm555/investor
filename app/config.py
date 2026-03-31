from typing import Optional

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
    langgraph_checkpointer_url: Optional[str] = None
    approval_token_ttl_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="INVESTOR_",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
