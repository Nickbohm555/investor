from fastapi import FastAPI
import httpx

from app.agents.research import ResearchNode
from app.api.routes import router
from app.config import get_settings
from app.db.models import Base
from app.db.session import get_session_factory
from app.graph.runtime import InvestorRuntime
from app.graph.workflow import compile_workflow
from app.services.broker_prestage import BrokerPrestageService
from app.services.mail_provider import SmtpMailProvider
from app.services.run_service import RunService


class StaticLLM:
    def invoke(self, _: dict[str, str]) -> str:
        return (
            '{"outcome":"candidates","recommendations":['
            '{"ticker":"NVDA","action":"buy","conviction_score":0.81,"supporting_evidence":["Congress buy","Insider buy"],'
            '"opposing_evidence":[],"risk_notes":["Volatile"],'
            '"source_summary":["Congress and insider signals aligned"],"broker_eligible":true}'
            ']}'
        )


def _static_quiver_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        payloads = {
            "/beta/live/congresstrading": [{"Ticker": "NVDA", "Transaction": "Purchase"}],
            "/beta/live/insiders": [{"Ticker": "NVDA", "Transaction": "Buy"}],
            "/beta/live/govcontracts": [{"Ticker": "NVDA", "Agency": "NASA", "Amount": "1000"}],
            "/beta/live/lobbying": [{"Ticker": "NVDA", "Client": "Example Client", "Issue": "Semiconductors"}],
        }
        return httpx.Response(200, json=payloads[request.url.path])

    return httpx.MockTransport(handler)


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
    Base.metadata.create_all(bind=session_factory.kw["bind"])
    run_service = RunService(session_factory)
    research_node = research_node or ResearchNode(llm=StaticLLM())
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
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.run_service = run_service
    app.state.runtime = runtime
    app.state.research_node = research_node
    app.state.mail_provider = mail_provider
    app.state.broker_prestage_service = broker_prestage_service
    app.state.quiver_transport = quiver_transport if quiver_transport is not None else _static_quiver_transport()
    app.include_router(router)

    return app


app = create_app()
