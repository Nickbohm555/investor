from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import RunRecord


NEW_YORK = ZoneInfo("America/New_York")


def build_schedule_key(now: datetime) -> str:
    market_date = now.astimezone(NEW_YORK).date().isoformat()
    return f"daily:{market_date}"


def create_or_get_scheduled_run(
    session: Session,
    now: datetime | None = None,
    run_factory=None,
) -> tuple[RunRecord, bool]:
    schedule_now = now or datetime.now(tz=NEW_YORK)
    schedule_key = build_schedule_key(schedule_now)
    run = run_factory(schedule_key)
    session.add(run)
    try:
        session.commit()
        session.refresh(run)
        return run, False
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(RunRecord).where(RunRecord.schedule_key == schedule_key))
        if existing is None:
            raise
        return existing, True
