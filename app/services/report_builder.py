from __future__ import annotations

from app.schemas.reports import StrategicInsightReport
from app.schemas.research import ResearchOutcome


def build_strategic_insight_report(
    *,
    run_id: str,
    outcome: ResearchOutcome,
    baseline_run_id: str | None,
    baseline_outcome: ResearchOutcome | None,
) -> StrategicInsightReport:
    raise NotImplementedError
