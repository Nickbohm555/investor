import importlib
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script.revision import Revision, RevisionMap
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import (
    ApprovalEventRecord,
    Base,
    BrokerArtifactRecord,
    RecommendationRecord,
    RunRecord,
    StateTransitionRecord,
)
from app.db.session import get_session_factory
from app.repositories.broker_artifacts import BrokerArtifactsRepository
from app.schemas.broker import BrokerMode, BrokerPolicySnapshot, OrderProposal
from app.schemas.workflow import Recommendation
from app.services.run_service import RunService


def _load_revision(module_name: str) -> Revision:
    module = importlib.import_module(module_name)
    return Revision(
        revision=module.revision,
        down_revision=module.down_revision,
    )


def test_create_run_record_persists_status():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run = RunRecord(
            run_id="run-123",
            thread_id="thread-123",
            status="created",
            trigger_source="manual",
            approval_status="pending",
            current_step="research",
        )
        session.add(run)
        session.commit()

        stored = session.get(RunRecord, "run-123")

    assert stored is not None
    assert stored.status == "created"
    assert stored.thread_id == "thread-123"


def test_runtime_models_include_durable_run_state_columns():
    run_columns = RunRecord.__table__.columns

    assert run_columns["thread_id"].type.length == 128
    assert not run_columns["thread_id"].nullable
    assert run_columns["trigger_source"].type.length == 32
    assert not run_columns["trigger_source"].nullable
    assert run_columns["approval_status"].type.length == 32
    assert not run_columns["approval_status"].nullable
    assert run_columns["current_step"].type.length == 64
    assert not run_columns["current_step"].nullable
    assert not run_columns["updated_at"].nullable


def test_related_runtime_tables_reference_runs_and_audit_fields():
    recommendation_columns = RecommendationRecord.__table__.columns
    approval_columns = ApprovalEventRecord.__table__.columns
    transition_columns = StateTransitionRecord.__table__.columns
    broker_columns = BrokerArtifactRecord.__table__.columns

    assert not recommendation_columns["created_at"].nullable
    assert approval_columns["token_id"].unique is True
    assert not approval_columns["occurred_at"].nullable
    assert not transition_columns["occurred_at"].nullable
    assert transition_columns["reason"].nullable
    assert broker_columns["client_order_id"].unique is True
    assert not broker_columns["policy_snapshot_json"].nullable


def test_initial_migration_creates_expected_runtime_columns():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    run_columns = {column["name"] for column in inspector.get_columns("runs")}
    recommendation_columns = {
        column["name"] for column in inspector.get_columns("recommendations")
    }
    approval_columns = {column["name"] for column in inspector.get_columns("approval_events")}
    transition_columns = {
        column["name"] for column in inspector.get_columns("state_transitions")
    }
    broker_columns = {
        column["name"] for column in inspector.get_columns("broker_artifacts")
    }

    assert {
        "thread_id",
        "trigger_source",
        "approval_status",
        "current_step",
        "updated_at",
    }.issubset(run_columns)
    assert {"created_at"}.issubset(recommendation_columns)
    assert {"token_id", "occurred_at"}.issubset(approval_columns)
    assert {"occurred_at", "reason"}.issubset(transition_columns)
    assert {
        "run_id",
        "recommendation_id",
        "broker_mode",
        "client_order_id",
        "policy_snapshot_json",
    }.issubset(broker_columns)


def test_settings_expose_runtime_persistence_configuration():
    settings = Settings()

    assert settings.database_url
    assert settings.langgraph_checkpointer_url is None
    assert settings.approval_token_ttl_seconds == 900


def test_create_pending_run_persists_supplied_runtime_state():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)

    created = service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )

    assert created.run_id == "run-123"

    with session_factory() as session:
        stored = session.get(RunRecord, "run-123")

    assert stored is not None
    assert stored.thread_id == "thread-123"
    assert stored.status == "triggered"
    assert stored.current_step == "research"


def test_store_recommendations_and_transition_share_same_run():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)
    service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )

    service.store_recommendations(
        "run-123",
        [
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.82,
                rationale="Durable infrastructure demand remains strong.",
            )
        ],
    )
    service.mark_status(
        "run-123",
        to_status="awaiting_review",
        current_step="approval",
        reason="Recommendations ready for operator review",
    )

    with session_factory() as session:
        recommendations = session.query(RecommendationRecord).filter_by(run_id="run-123").all()
        transitions = session.query(StateTransitionRecord).filter_by(run_id="run-123").all()
        stored = session.get(RunRecord, "run-123")

    assert stored is not None
    assert stored.status == "awaiting_review"
    assert stored.current_step == "approval"
    assert len(recommendations) == 1
    assert recommendations[0].ticker == "NVDA"
    assert len(transitions) == 1
    assert transitions[0].from_status == "triggered"
    assert transitions[0].to_status == "awaiting_review"


def test_record_approval_event_rejects_duplicate_token_ids():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)
    service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="awaiting_review",
        current_step="approval",
        trigger_source="manual",
    )

    service.record_approval_event("run-123", decision="approve", token_id="token-123")

    with pytest.raises(IntegrityError):
        service.record_approval_event("run-123", decision="approve", token_id="token-123")


def test_run_service_persists_completed_lifecycle_with_approval_event_and_transitions():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)

    service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="triggered",
        current_step="research",
        trigger_source="manual",
    )
    service.store_recommendations(
        "run-123",
        [
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.82,
                rationale="Durable infrastructure demand remains strong.",
            )
        ],
    )
    service.mark_status(
        "run-123",
        to_status="awaiting_review",
        current_step="approval",
        reason="Recommendations ready for operator review",
    )
    approval_state = service.apply_approval_decision(
        "run-123",
        decision="approve",
        token_id="token-approve-123",
    )
    service.mark_status(
        "run-123",
        to_status="completed",
        current_step="completed",
        reason="Approved run handed off successfully",
        approval_status="approved",
    )

    assert approval_state["status"] == "approved"

    with session_factory() as session:
        run = session.get(RunRecord, "run-123")
        recommendations = session.query(RecommendationRecord).filter_by(run_id="run-123").all()
        approval_events = session.query(ApprovalEventRecord).filter_by(run_id="run-123").all()
        transitions = (
            session.query(StateTransitionRecord)
            .filter_by(run_id="run-123")
            .order_by(StateTransitionRecord.id.asc())
            .all()
        )

    assert run is not None
    assert run.status == "completed"
    assert run.approval_status == "approved"
    assert len(recommendations) == 1
    assert len(approval_events) == 1
    assert [transition.to_status for transition in transitions] == [
        "awaiting_review",
        "approved",
        "completed",
    ]


def test_broker_artifact_persists_run_recommendation_and_policy_snapshot():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)
    service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="awaiting_review",
        current_step="approval",
        trigger_source="manual",
    )
    recommendation = service.store_recommendations(
        "run-123",
        [
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.82,
                rationale="Durable infrastructure demand remains strong.",
            )
        ],
    )[0]

    proposal = OrderProposal(
        run_id="run-123",
        recommendation_id=recommendation.id,
        broker_mode=BrokerMode.paper,
        symbol="NVDA",
        side="buy",
        order_type="market",
        time_in_force="day",
        qty=None,
        notional="250.00",
        client_order_id="run-123-1-paper",
    )
    snapshot = BrokerPolicySnapshot(
        broker_mode=BrokerMode.paper,
        account_buying_power="1000.00",
        asset_tradable=True,
        asset_fractionable=True,
        order_shape={"side": "buy", "order_type": "market", "time_in_force": "day"},
    )

    with session_factory.begin() as session:
        repository = BrokerArtifactsRepository(session)
        artifact = repository.create_artifact(proposal, snapshot)

    with session_factory() as session:
        stored = session.query(BrokerArtifactRecord).filter_by(client_order_id="run-123-1-paper").one()

    assert artifact.run_id == "run-123"
    assert stored.recommendation_id == recommendation.id
    assert stored.broker_mode == "paper"
    assert stored.policy_snapshot_json["broker_mode"] == "paper"
    assert stored.client_order_id == "run-123-1-paper"


def test_broker_artifact_client_order_id_must_be_unique():
    session_factory = get_session_factory("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_factory.kw["bind"])
    service = RunService(session_factory)
    service.create_pending_run(
        run_id="run-123",
        thread_id="thread-123",
        status="awaiting_review",
        current_step="approval",
        trigger_source="manual",
    )
    recommendation = service.store_recommendations(
        "run-123",
        [
            Recommendation(
                ticker="NVDA",
                action="buy",
                conviction_score=0.82,
                rationale="Durable infrastructure demand remains strong.",
            )
        ],
    )[0]

    proposal = OrderProposal(
        run_id="run-123",
        recommendation_id=recommendation.id,
        broker_mode=BrokerMode.paper,
        symbol="NVDA",
        side="buy",
        order_type="market",
        time_in_force="day",
        qty=None,
        notional="250.00",
        client_order_id="run-123-1-paper",
    )
    snapshot = BrokerPolicySnapshot(
        broker_mode=BrokerMode.paper,
        account_buying_power="1000.00",
        asset_tradable=True,
        asset_fractionable=True,
        order_shape={"side": "buy", "order_type": "market", "time_in_force": "day"},
    )

    with session_factory.begin() as session:
        repository = BrokerArtifactsRepository(session)
        repository.create_artifact(proposal, snapshot)

    with pytest.raises(IntegrityError):
        with session_factory.begin() as session:
            repository = BrokerArtifactsRepository(session)
            repository.create_artifact(proposal, snapshot)


def test_alembic_branch_merge_produces_single_head(monkeypatch, tmp_path):
    revision_map = RevisionMap(
        lambda: [
            _load_revision("app.db.migrations.versions.0001_create_run_tables"),
            _load_revision("app.db.migrations.versions.0002_add_schedule_fields"),
            _load_revision("app.db.migrations.versions.0002_create_broker_artifacts"),
            _load_revision("app.db.migrations.versions.0003_merge_phase5_heads"),
        ]
    )

    assert revision_map.heads == ("0003_merge_phase5_heads",)

    database_path = tmp_path / "alembic-merge.sqlite"
    monkeypatch.setenv("INVESTOR_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "app" / "db" / "migrations"),
    )

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database_path}", future=True)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= {
        "runs",
        "recommendations",
        "approval_events",
        "state_transitions",
        "broker_artifacts",
    }
