"""create run tables

Revision ID: 0001_create_run_tables
Revises:
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_run_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(length=64), primary_key=True),
        sa.Column("thread_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_source", sa.String(length=32), nullable=False),
        sa.Column(
            "approval_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("current_step", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "approval_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("token_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "state_transitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("state_transitions")
    op.drop_table("approval_events")
    op.drop_table("recommendations")
    op.drop_table("runs")
