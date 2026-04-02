from __future__ import annotations


class OperationEventsRepository:
    def create_event(self, *args, **kwargs):
        raise NotImplementedError

    def list_run_events(self, run_id: str):
        raise NotImplementedError
