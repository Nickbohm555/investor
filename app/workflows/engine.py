from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import BrokerArtifactRecord
from app.graph.workflow import compile_workflow
from app.repositories.runs import RunsRepository
from app.schemas.research import CandidateRecommendation
from app.services.handoff import build_alpaca_handoff
from app.tools.alpaca import AlpacaClient
from app.workflows.state import WorkflowEvent, WorkflowResult


class WorkflowEngine:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        research_node: object,
        settings: object,
        mail_provider: object,
        alpaca_client_factory: Callable[[str], object] | None = None,
        workflow_factory: Callable[..., object] = compile_workflow,
    ) -> None:
        self._session_factory = session_factory
        self._research_node = research_node
        self._settings = settings
        self._mail_provider = mail_provider
        self._alpaca_client_factory = alpaca_client_factory or self._default_alpaca_client_factory
        self._workflow_factory = workflow_factory

    def start_run(self, *, run_id: str, quiver_client: object, baseline_report: dict | None = None) -> dict:
        workflow = self._compile_workflow()
        with self._session_factory.begin() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            result = workflow.invoke(
                {
                    "run_id": run_id,
                    "quiver_client": quiver_client,
                    "baseline_report": baseline_report,
                }
            )
            serialized_result = WorkflowResult(
                status=result["status"],
                current_step=result["current_step"],
                state_payload=result,
            ).to_dict()
            repository.update_state_payload(run, serialized_result["state_payload"])
            repository.transition_run(
                run,
                to_status=serialized_result["status"],
                current_step=serialized_result["current_step"],
                reason="Research completed and awaiting operator review",
            )
        return serialized_result

    def advance_run(self, *, run_id: str, event: str) -> dict:
        if event not in {"approval:approve", "approval:reject", "execution:confirm"}:
            raise ValueError(f"Unsupported workflow event: {event}")
        with self._session_factory.begin() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            if run.state_payload is None:
                raise ValueError(f"Run {run_id} has no persisted workflow state")

            state_payload = dict(run.state_payload)
            if event == "approval:reject":
                result = WorkflowResult(
                    status="rejected",
                    current_step="rejected",
                    state_payload={
                        **state_payload,
                        "status": "rejected",
                        "current_step": "rejected",
                    },
                ).to_dict()
            elif event == "approval:approve":
                recommendations = [
                    item
                    if isinstance(item, CandidateRecommendation)
                    else CandidateRecommendation.model_validate(item)
                    for item in state_payload.get("recommendations", [])
                ]
                handoff = build_alpaca_handoff(run_id, recommendations)
                result = WorkflowResult(
                    status="broker_prestaged",
                    current_step="broker_prestaged",
                    state_payload={
                        **state_payload,
                        "status": "broker_prestaged",
                        "current_step": "broker_prestaged",
                        "handoff": handoff,
                    },
                    handoff=handoff,
                ).to_dict()
            else:
                if run.status != "broker_prestaged" or run.current_step != "broker_prestaged":
                    raise ValueError(
                        "Run must already be broker_prestaged before execution confirmation"
                    )

                broker_artifacts = (
                    session.query(BrokerArtifactRecord)
                    .filter(BrokerArtifactRecord.run_id == run_id)
                    .order_by(BrokerArtifactRecord.recommendation_id.asc())
                    .all()
                )
                if not broker_artifacts:
                    raise ValueError(f"Run {run_id} has no broker artifacts to submit")

                alpaca_client = self._alpaca_client_factory(self._settings.broker_mode)
                submitted_orders: list[dict] = []
                for artifact in broker_artifacts:
                    response = alpaca_client.submit_order(
                        symbol=artifact.symbol,
                        side=artifact.side,
                        order_type=artifact.order_type,
                        time_in_force=artifact.time_in_force,
                        client_order_id=artifact.client_order_id,
                        notional=artifact.notional,
                        qty=artifact.qty,
                    )
                    artifact.status = "submitted"
                    submitted_orders.append(
                        {
                            "recommendation_id": artifact.recommendation_id,
                            "symbol": artifact.symbol,
                            "side": artifact.side,
                            "client_order_id": artifact.client_order_id,
                            "broker_order_id": response.get("id"),
                            "broker_status": response.get("status"),
                        }
                    )

                result = WorkflowResult(
                    status="submitted",
                    current_step="submitted",
                    state_payload={
                        **state_payload,
                        "status": "submitted",
                        "current_step": "submitted",
                        "submitted_orders": submitted_orders,
                        "submitted_order_count": len(submitted_orders),
                    },
                ).to_dict()
                result["submitted_order_count"] = len(submitted_orders)

            repository.update_state_payload(run, result["state_payload"])
            repository.transition_run(
                run,
                to_status=result["status"],
                current_step=result["current_step"],
                approval_status=event.split(":", 1)[1] if event.startswith("approval:") else None,
                reason=f"Workflow advanced via {event}",
            )
        return result

    def _compile_workflow(self):
        return self._workflow_factory(
            self._research_node,
            self._settings,
            self._mail_provider,
        )

    def _default_alpaca_client_factory(self, broker_mode: str) -> AlpacaClient:
        _ = broker_mode
        return AlpacaClient(
            base_url=self._settings.alpaca_base_url,
            api_key=self._settings.alpaca_api_key,
        )

    def _require_run(self, repository: RunsRepository, run_id: str):
        run = repository.get_run(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        return run
