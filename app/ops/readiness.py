from __future__ import annotations

from app.config import Settings


def collect_readiness_errors(settings: Settings) -> list[str]:
    return []


def assert_startup_readiness(settings: Settings, session_factory) -> None:
    return None
