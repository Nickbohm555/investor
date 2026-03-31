from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import (
    ApprovalEventRecord,
    Base,
    RecommendationRecord,
    RunRecord,
    StateTransitionRecord,
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

    assert not recommendation_columns["created_at"].nullable
    assert approval_columns["token_id"].unique is True
    assert not approval_columns["occurred_at"].nullable
    assert not transition_columns["occurred_at"].nullable
    assert transition_columns["reason"].nullable


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


def test_settings_expose_runtime_persistence_configuration():
    settings = Settings()

    assert settings.database_url
    assert settings.langgraph_checkpointer_url is None
    assert settings.approval_token_ttl_seconds == 900
