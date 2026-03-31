"""phase 6 workflow engine schema

Revision ID: 0004_phase6_workflow_engine_schema
Revises: 0003_merge_phase5_heads
Create Date: 2026-03-31
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "0004_phase6_workflow_engine_schema"
down_revision = "0003_merge_phase5_heads"
branch_labels = None
depends_on = None

ARCHIVED_STATUS = "archived_pre_phase6"
ARCHIVE_MARKER = {
    "legacy_runtime": "langgraph",
    "archived_reason": "phase6_cutover",
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    run_columns = {column["name"] for column in inspector.get_columns("runs")}

    if "state_payload" not in run_columns:
        with op.batch_alter_table("runs") as batch_op:
            batch_op.add_column(sa.Column("state_payload", sa.JSON(), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE runs
            SET status = :archived_status,
                current_step = :archived_status,
                approval_status = 'archived',
                state_payload = :archive_marker
            WHERE thread_id IS NOT NULL
               OR current_step IN ('approval', 'resuming')
               OR status IN ('awaiting_review', 'resuming')
            """
        ),
        {
            "archived_status": ARCHIVED_STATUS,
            "archive_marker": json.dumps(ARCHIVE_MARKER),
        },
    )

    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("thread_id")


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("thread_id", sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint("uq_runs_thread_id", ["thread_id"])
