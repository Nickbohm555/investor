"""add schedule fields

Revision ID: 0002_add_schedule_fields
Revises: 0001_create_run_tables
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_schedule_fields"
down_revision = "0001_create_run_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("schedule_key", sa.String(length=32), nullable=True))
    op.add_column("runs", sa.Column("replay_of_run_id", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_runs_schedule_key", "runs", ["schedule_key"])


def downgrade() -> None:
    op.drop_constraint("uq_runs_schedule_key", "runs", type_="unique")
    op.drop_column("runs", "replay_of_run_id")
    op.drop_column("runs", "schedule_key")
