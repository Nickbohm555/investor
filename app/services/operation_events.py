from __future__ import annotations


class OperationEventService:
    def __init__(self, session_factory, secrets) -> None:
        self.session_factory = session_factory
        self.secrets = secrets

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
    ):
        raise NotImplementedError

    def list_run_events(self, run_id: str):
        raise NotImplementedError
