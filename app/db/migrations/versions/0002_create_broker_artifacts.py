"""create broker artifacts

Revision ID: 0002_create_broker_artifacts
Revises: 0001_create_run_tables
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_create_broker_artifacts"
down_revision = "0001_create_run_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("broker_mode", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("order_type", sa.String(length=16), nullable=False),
        sa.Column("time_in_force", sa.String(length=16), nullable=False),
        sa.Column("qty", sa.String(length=32), nullable=True),
        sa.Column("notional", sa.String(length=32), nullable=True),
        sa.Column("client_order_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("policy_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("client_order_id", name="uq_broker_artifacts_client_order_id"),
    )


def downgrade() -> None:
    op.drop_table("broker_artifacts")
