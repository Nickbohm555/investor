from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

from app.schemas.reports import StrategicInsightReport
from app.schemas.workflow import RecommendationEmail


def build_report_environment(template_dir: str | Path | None = None) -> Environment:
    raise NotImplementedError


def render_report_email(
    *, report: StrategicInsightReport, approval_url: str, rejection_url: str
) -> RecommendationEmail:
    raise NotImplementedError
