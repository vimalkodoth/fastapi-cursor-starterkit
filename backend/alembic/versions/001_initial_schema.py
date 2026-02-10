"""Initial schema: data_processing_records and task_logs

Revision ID: 001_initial
Revises:
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_processing_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "task_type", sa.String(length=255), nullable=False, server_default="data"
        ),
        sa.Column("task_status", sa.String(length=255), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_data_processing_records_task_id"),
        "data_processing_records",
        ["task_id"],
        unique=False,
    )

    op.create_table(
        "task_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("queue_name", sa.String(length=255), nullable=True),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_logs_correlation_id"),
        "task_logs",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_logs_task_id"), "task_logs", ["task_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_logs_task_id"), table_name="task_logs")
    op.drop_index(op.f("ix_task_logs_correlation_id"), table_name="task_logs")
    op.drop_table("task_logs")
    op.drop_index(
        op.f("ix_data_processing_records_task_id"), table_name="data_processing_records"
    )
    op.drop_table("data_processing_records")
