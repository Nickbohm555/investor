from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import OperationEventRecord


class OperationEventsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(
        self,
        *,
        run_id: str,
        stage: str,
        provider: str,
        outcome: str,
        error_code: str | None = None,
        http_status: int | None = None,
        detail: str | None = None,
        trace_id: str | None = None,
    ) -> OperationEventRecord:
        event = OperationEventRecord(
            run_id=run_id,
            stage=stage,
            provider=provider,
            outcome=outcome,
            error_code=error_code,
            http_status=http_status,
            detail=detail,
            trace_id=trace_id,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_run_events(self, run_id: str) -> list[OperationEventRecord]:
        return (
            self.session.query(OperationEventRecord)
            .filter_by(run_id=run_id)
            .order_by(OperationEventRecord.id.desc())
            .all()
        )
