from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from app.agents.research import ResearchNode
from app.config import Settings
from app.schemas.research_agent import ResearchAgentBudget
from app.services.approvals import ApprovalService
from app.services.broker_prestage import BrokerPrestageService
from app.services.mail_provider import SmtpMailProvider
from app.services.research_llm import HttpResearchLLM
from app.services.run_service import RunService
from app.tools.quiver import QuiverClient
from app.workflows.engine import WorkflowEngine


@dataclass
class AppRuntime:
    settings: Settings
    session_factory: sessionmaker[Session]
    run_service: RunService
    workflow_engine: WorkflowEngine
    research_node: ResearchNode
    mail_provider: object
    broker_prestage_service: BrokerPrestageService
    approval_service: ApprovalService
    quiver_transport: object | None = None

    def create_quiver_client(self) -> QuiverClient:
        return QuiverClient(
            base_url=self.settings.quiver_base_url,
            api_key=self.settings.quiver_api_key,
            transport=self.quiver_transport,
        )


def build_runtime(
    *,
    settings: Settings,
    session_factory: sessionmaker[Session],
    workflow_engine: WorkflowEngine | None = None,
    research_node: ResearchNode | None = None,
    quiver_transport: object | None = None,
    mail_provider: object | None = None,
    alpaca_client_factory: Callable[[str], object] | None = None,
    broker_prestage_service: BrokerPrestageService | None = None,
) -> AppRuntime:
    run_service = RunService(session_factory)
    research_node = research_node or ResearchNode(
        llm=HttpResearchLLM(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        ),
        budget=ResearchAgentBudget(
            max_steps=settings.research_agent_max_steps,
            max_tool_calls=settings.research_agent_max_tool_calls,
            max_seed_tickers=settings.research_agent_max_seed_tickers,
        ),
    )
    mail_provider = mail_provider or SmtpMailProvider(settings)
    workflow_engine = workflow_engine or WorkflowEngine(
        session_factory=session_factory,
        research_node=research_node,
        settings=settings,
        mail_provider=mail_provider,
        alpaca_client_factory=alpaca_client_factory,
    )
    broker_prestage_service = broker_prestage_service or BrokerPrestageService(
        session_factory=session_factory,
        settings=settings,
        alpaca_client_factory=alpaca_client_factory,
    )
    approval_service = ApprovalService(
        session_factory=session_factory,
        workflow_engine=workflow_engine,
        prestage_service=broker_prestage_service.prestage_approved_recommendations,
        broker_mode=settings.broker_mode,
    )
    return AppRuntime(
        settings=settings,
        session_factory=session_factory,
        run_service=run_service,
        workflow_engine=workflow_engine,
        research_node=research_node,
        mail_provider=mail_provider,
        broker_prestage_service=broker_prestage_service,
        approval_service=approval_service,
        quiver_transport=quiver_transport,
    )
