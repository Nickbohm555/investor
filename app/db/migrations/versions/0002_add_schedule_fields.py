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
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("schedule_key", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("replay_of_run_id", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_runs_schedule_key", ["schedule_key"])


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint("uq_runs_schedule_key", type_="unique")
        batch_op.drop_column("replay_of_run_id")
        batch_op.drop_column("schedule_key")
