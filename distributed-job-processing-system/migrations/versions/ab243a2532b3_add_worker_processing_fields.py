"""Add fields required for worker processing.

Revision ID: ab243a2532b3
Revises: b63bc8dd8717
Create Date: 2026-09-10 17:15:22.610554
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Alembic uses these identifiers to determine migration order.
revision: str = "ab243a2532b3"
down_revision: str | Sequence[str] | None = "b63bc8dd8717"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add worker ownership, execution results, and processing timestamps."""

    # The server default safely initializes jobs created before this migration.
    op.add_column(
        "jobs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "worker_id",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Alembic does not always detect new check constraints on existing tables.
    op.create_check_constraint(
        "ck_jobs_attempt_count_nonnegative",
        "jobs",
        "attempt_count >= 0",
    )


def downgrade() -> None:
    """Remove worker-processing fields in reverse dependency order."""

    # The constraint must be removed before its column.
    op.drop_constraint(
        "ck_jobs_attempt_count_nonnegative",
        "jobs",
        type_="check",
    )
    op.drop_column("jobs", "completed_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("jobs", "last_error")
    op.drop_column("jobs", "result")
    op.drop_column("jobs", "worker_id")
    op.drop_column("jobs", "attempt_count")
