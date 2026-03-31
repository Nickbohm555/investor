from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_default_engine():
    return create_engine(get_settings().database_url, future=True)


def get_engine(database_url: Optional[str] = None):
    if database_url is not None:
        return create_engine(database_url, future=True)
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
