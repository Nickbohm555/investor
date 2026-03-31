from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "investor"
    app_env: str = "development"
    app_secret: str = "change-me"
    database_url: str = "sqlite+pysqlite:///./investor.db"
    langgraph_checkpointer_url: Optional[str] = None
    approval_token_ttl_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="INVESTOR_",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
