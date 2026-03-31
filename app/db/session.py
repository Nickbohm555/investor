from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_default_engine():
    return _create_engine(get_settings().database_url)


def _create_engine(database_url: str):
    if database_url == "sqlite+pysqlite:///:memory:":
        return create_engine(
            database_url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(database_url, future=True)


def get_engine(database_url: Optional[str] = None):
    if database_url is not None:
        return _create_engine(database_url)
    return _get_default_engine()


def get_session_factory(database_url: Optional[str] = None) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), expire_on_commit=False, class_=Session)


def get_db_session() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
