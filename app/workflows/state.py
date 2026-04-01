from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

WorkflowEvent = Literal["approval:approve", "approval:reject", "execution:confirm"]


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return {key: _serialize_value(item) for key, item in value.model_dump(mode="python").items()}
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


@dataclass
class WorkflowResult:
    status: str
    current_step: str
    state_payload: dict[str, Any] = field(default_factory=dict)
    handoff: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "current_step": self.current_step,
            "state_payload": _serialize_value(self.state_payload),
        }
        if self.handoff is not None:
            result["handoff"] = _serialize_value(self.handoff)
        return result
