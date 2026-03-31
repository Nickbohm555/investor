from fastapi import FastAPI

from app.agents.research import ResearchNode
from app.api.routes import router
from app.config import get_settings
from app.db.models import Base
from app.db.session import get_session_factory
from app.graph.runtime import InvestorRuntime
from app.services.run_service import RunService


class StaticLLM:
    def invoke(self, _: dict[str, str]) -> str:
        return (
            '{"recommendations": ['
            '{"ticker": "NVDA", "action": "buy", "conviction_score": 0.81, "rationale": "signal"}'
            "]}"
        )


def create_app(
    *,
    settings=None,
    session_factory=None,
    runtime=None,
    research_node=None,
) -> FastAPI:
    settings = settings or get_settings()
    session_factory = session_factory or get_session_factory(settings.database_url)
    Base.metadata.create_all(session_factory.kw["bind"])
    run_service = RunService(session_factory)
    runtime = runtime or InvestorRuntime(settings=settings)
    research_node = research_node or ResearchNode(llm=StaticLLM())
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.run_service = run_service
    app.state.runtime = runtime
    app.state.research_node = research_node
    app.include_router(router)

    return app


app = create_app()
