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
        if event == "execution:confirm":
            return self._confirm_execution(run_id=run_id)
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

    def _confirm_execution(self, *, run_id: str) -> dict:
        with self._session_factory() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            if run.state_payload is None:
                raise ValueError(f"Run {run_id} has no persisted workflow state")
            if run.status == "submitted" or run.current_step == "submitted":
                raise ValueError("Run has already been submitted")
            if run.status != "broker_prestaged" or run.current_step != "broker_prestaged":
                raise ValueError("Run must already be broker_prestaged before execution confirmation")

            broker_artifacts = (
                session.query(BrokerArtifactRecord)
                .filter(BrokerArtifactRecord.run_id == run_id)
                .order_by(BrokerArtifactRecord.recommendation_id.asc())
                .all()
            )
            if not broker_artifacts:
                raise ValueError(f"Run {run_id} has no broker artifacts to submit")
            if any(artifact.status == "submission_in_flight" for artifact in broker_artifacts):
                raise ValueError("Execution reconciliation required before submission can resume")

            total_artifacts = len(broker_artifacts)
            remaining_artifact_ids = [
                artifact.id for artifact in broker_artifacts if artifact.status != "submitted"
            ]

        alpaca_client = self._alpaca_client_factory(self._settings.broker_mode)

        for artifact_id in remaining_artifact_ids:
            artifact = self._mark_artifact_submission_in_flight(run_id=run_id, artifact_id=artifact_id)
            try:
                response = alpaca_client.submit_order(
                    symbol=artifact.symbol,
                    side=artifact.side,
                    order_type=artifact.order_type,
                    time_in_force=artifact.time_in_force,
                    client_order_id=artifact.client_order_id,
                    notional=artifact.notional,
                    qty=artifact.qty,
                )
            except Exception as exc:
                self._mark_run_reconciliation_required(run_id=run_id)
                raise ValueError("Execution reconciliation required after broker submission failure") from exc

            self._record_submitted_artifact(
                run_id=run_id,
                artifact_id=artifact_id,
                response=response,
                total_artifacts=total_artifacts,
            )

        with self._session_factory() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            state_payload = dict(run.state_payload or {})
            return {
                "status": run.status,
                "current_step": run.current_step,
                "state_payload": state_payload,
                "submitted_order_count": state_payload.get("submitted_order_count", 0),
            }

    def _mark_artifact_submission_in_flight(self, *, run_id: str, artifact_id: int) -> BrokerArtifactRecord:
        with self._session_factory.begin() as session:
            artifact = (
                session.query(BrokerArtifactRecord)
                .filter(
                    BrokerArtifactRecord.run_id == run_id,
                    BrokerArtifactRecord.id == artifact_id,
                )
                .one()
            )
            if artifact.status == "submitted":
                return artifact
            artifact.status = "submission_in_flight"
            session.flush()
            session.expunge(artifact)
            return artifact

    def _record_submitted_artifact(
        self,
        *,
        run_id: str,
        artifact_id: int,
        response: dict,
        total_artifacts: int,
    ) -> None:
        with self._session_factory.begin() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            artifact = (
                session.query(BrokerArtifactRecord)
                .filter(
                    BrokerArtifactRecord.run_id == run_id,
                    BrokerArtifactRecord.id == artifact_id,
                )
                .one()
            )
            artifact.status = "submitted"

            state_payload = dict(run.state_payload or {})
            submitted_orders = list(state_payload.get("submitted_orders", []))
            submitted_orders = [
                order for order in submitted_orders if order.get("client_order_id") != artifact.client_order_id
            ]
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

            is_complete = len(submitted_orders) == total_artifacts
            next_status = "submitted" if is_complete else "broker_prestaged"
            next_step = "submitted" if is_complete else "broker_prestaged"
            repository.update_state_payload(
                run,
                {
                    **state_payload,
                    "status": next_status,
                    "current_step": next_step,
                    "submitted_orders": submitted_orders,
                    "submitted_order_count": len(submitted_orders),
                },
            )
            if is_complete:
                repository.transition_run(
                    run,
                    to_status="submitted",
                    current_step="submitted",
                    reason="Workflow advanced via execution:confirm",
                )

    def _mark_run_reconciliation_required(self, *, run_id: str) -> None:
        with self._session_factory.begin() as session:
            repository = RunsRepository(session)
            run = self._require_run(repository, run_id)
            state_payload = dict(run.state_payload or {})
            repository.update_state_payload(
                run,
                {
                    **state_payload,
                    "execution_status": "reconciliation_required",
                },
            )

    def _require_run(self, repository: RunsRepository, run_id: str):
        run = repository.get_run(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        return run
