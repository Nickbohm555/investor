from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.schemas.reports import StrategicInsightReport
from app.schemas.workflow import RecommendationEmail


def build_report_environment(template_dir: str | Path | None = None) -> Environment:
    loader_root = Path(template_dir) if template_dir is not None else Path("app/templates/reports")
    return Environment(
        loader=FileSystemLoader(str(loader_root)),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
    )


def render_report_email(*, report: StrategicInsightReport, approval_url: str, rejection_url: str) -> RecommendationEmail:
    environment = build_report_environment()
    payload = {
        "report": report.model_dump(),
        "approval_url": approval_url,
        "rejection_url": rejection_url,
    }
    return RecommendationEmail(
        subject=f"Investor strategic insight for {report.run_id}",
        body=environment.get_template("strategic_report.txt.j2").render(**payload),
        html_body=environment.get_template("strategic_report.html.j2").render(**payload),
    )
