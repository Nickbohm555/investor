from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db.models import Base
from app.db.session import get_session_factory
from app.ops.readiness import assert_startup_readiness
from app.runtime import build_runtime


def create_app(
    *,
    settings=None,
    session_factory=None,
    workflow_engine=None,
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
    runtime = build_runtime(
        settings=settings,
        session_factory=session_factory,
        workflow_engine=workflow_engine,
        research_node=research_node,
        quiver_transport=quiver_transport,
        mail_provider=mail_provider,
        alpaca_client_factory=alpaca_client_factory,
        broker_prestage_service=broker_prestage_service,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        assert_startup_readiness(settings, session_factory)
        _bind_runtime(app, runtime)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    _bind_runtime(app, runtime)
    app.include_router(router)

    return app


def _bind_runtime(app: FastAPI, runtime) -> None:
    app.state.runtime = runtime
    app.state.settings = runtime.settings
    app.state.session_factory = runtime.session_factory
    app.state.run_service = runtime.run_service
    app.state.workflow_engine = runtime.workflow_engine
    app.state.research_node = runtime.research_node
    app.state.mail_provider = runtime.mail_provider
    app.state.broker_prestage_service = runtime.broker_prestage_service
    app.state.approval_service = runtime.approval_service
    app.state.quiver_transport = runtime.quiver_transport


app = create_app()
