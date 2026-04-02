from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import OperationEventRecord
from app.repositories.operation_events import OperationEventsRepository

class OperationEventService:
    def __init__(self, session_factory: sessionmaker[Session], secrets: Sequence[str]) -> None:
        self.session_factory = session_factory
        self.secrets = tuple(secret for secret in secrets if secret)

    def record_event(
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
        with self.session_factory.begin() as session:
            return OperationEventsRepository(session).create_event(
                run_id=run_id,
                stage=stage,
                provider=provider,
                outcome=outcome,
                error_code=error_code,
                http_status=http_status,
                detail=self._mask_sensitive_values(detail),
                trace_id=trace_id,
            )

    def list_run_events(self, run_id: str) -> list[OperationEventRecord]:
        with self.session_factory() as session:
            return OperationEventsRepository(session).list_run_events(run_id)

    def _mask_sensitive_values(self, detail: str | None) -> str | None:
        if detail is None:
            return None

        masked = detail
        for secret in self.secrets:
            if secret:
                masked = masked.replace(secret, "***redacted***")
        return masked
