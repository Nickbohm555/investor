"""phase 17 operation events

Revision ID: 0005_phase17_operation_events
Revises: 0004_phase6_workflow_engine_schema
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_phase17_operation_events"
down_revision = "0004_phase6_workflow_engine_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operation_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("operation_events")
