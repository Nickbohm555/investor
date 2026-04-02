from app.schemas.reports import StrategicInsightReport
from app.schemas.workflow import RecommendationEmail
from app.services.report_render import render_report_email

def compose_report_email(*, report: StrategicInsightReport, approval_url: str, rejection_url: str) -> RecommendationEmail:
    return render_report_email(
        report=report,
        approval_url=approval_url,
        rejection_url=rejection_url,
    )
