from pydantic import BaseModel, Field

from app.schemas.workflow import Recommendation


class WorkflowState(BaseModel):
    run_id: str
    status: str = "created"
    recommendations: list[Recommendation] = Field(default_factory=list)
    email_body: str = ""
    handoff: dict = Field(default_factory=dict)
