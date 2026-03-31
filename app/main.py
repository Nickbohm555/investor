from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.research import ResearchNode
from app.api.routes import router
from app.config import get_settings
from app.db.models import Base
from app.db.session import get_session_factory
from app.graph.runtime import InvestorRuntime
from app.graph.workflow import compile_workflow
from app.ops.readiness import assert_startup_readiness
from app.services.broker_prestage import BrokerPrestageService
from app.services.mail_provider import SmtpMailProvider
from app.services.research_llm import HttpResearchLLM
from app.services.run_service import RunService


def create_app(
    *,
    settings=None,
    session_factory=None,
    runtime=None,
    research_node=None,
    quiver_transport=None,
    mail_provider=None,
    alpaca_client_factory=None,
    broker_prestage_service=None,
) -> FastAPI:
    settings = settings or get_settings()
    session_factory = session_factory or get_session_factory(settings.database_url)
    assert_startup_readiness(settings, session_factory)
    Base.metadata.create_all(bind=session_factory.kw["bind"])
    run_service = RunService(session_factory)
    research_node = research_node or ResearchNode(
        llm=HttpResearchLLM(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    )
    mail_provider = mail_provider or SmtpMailProvider(settings)
    runtime = runtime or InvestorRuntime(
        settings=settings,
        mail_provider=mail_provider,
        workflow_factory=lambda research_node, settings, mail_provider, checkpointer, evidence_builder=None: compile_workflow(
            research_node, settings, mail_provider
        ),
    )
    broker_prestage_service = broker_prestage_service or BrokerPrestageService(
        session_factory=session_factory,
        settings=settings,
        alpaca_client_factory=alpaca_client_factory,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        assert_startup_readiness(settings, session_factory)
        app.state.settings = settings
        app.state.session_factory = session_factory
        app.state.run_service = run_service
        app.state.runtime = runtime
        app.state.research_node = research_node
        app.state.mail_provider = mail_provider
        app.state.broker_prestage_service = broker_prestage_service
        app.state.quiver_transport = quiver_transport
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.run_service = run_service
    app.state.runtime = runtime
    app.state.research_node = research_node
    app.state.mail_provider = mail_provider
    app.state.broker_prestage_service = broker_prestage_service
    app.state.quiver_transport = quiver_transport
    app.include_router(router)

    return app


app = create_app()
