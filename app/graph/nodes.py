from __future__ import annotations

from app.schemas.workflow import RecommendationEmail, ResearchResult
from app.services.email import compose_recommendation_email, send_console_email
from app.services.handoff import build_alpaca_handoff
from app.services.risk import filter_recommendations


def load_context(state: dict) -> dict:
    return state


def research(state: dict, research_node) -> ResearchResult:
    return research_node.run(account_context={"run_id": state["run_id"]})


def risk_filter(result: ResearchResult) -> list:
    return filter_recommendations(result.recommendations, minimum_conviction=0.6, max_ideas=3)


def compose_email(run_id: str, recommendations: list[object]) -> RecommendationEmail:
    return compose_recommendation_email(
        run_id=run_id,
        recommendations=recommendations,
        approval_url=f"http://localhost:8000/approval/{run_id}:approve",
        rejection_url=f"http://localhost:8000/approval/{run_id}:reject",
    )


def send_email(message: RecommendationEmail) -> RecommendationEmail:
    return send_console_email(message)


def await_human_review(state: dict, message: RecommendationEmail) -> dict:
    return {
        **state,
        "status": "awaiting_human_review",
        "email_body": message.body,
    }


def handoff_to_alpaca(state: dict) -> dict:
    return {
        **state,
        "handoff": build_alpaca_handoff(state["run_id"], state["recommendations"]),
    }


def finalize(state: dict) -> dict:
    return {**state, "status": "completed"}
