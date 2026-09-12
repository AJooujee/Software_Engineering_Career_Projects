"""Add retry scheduling fields.

Revision ID: f233f5d3a0fd
Revises: ab243a2532b3
Create Date: 2026-09-12 14:56:08.536303
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic uses these identifiers to determine migration order.
revision: str = "f233f5d3a0fd"
down_revision: str | Sequence[str] | None = "ab243a2532b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add retry limits, scheduling time, constraint, and claim index."""

    # Existing jobs receive safe defaults when these non-nullable columns are added.
    op.add_column(
        "jobs",
        sa.Column(
            "max_attempts",
            sa.Integer(),
            server_default="3",
            nullable=False,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Alembic does not always detect new check constraints automatically.
    op.create_check_constraint(
        "ck_jobs_max_attempts_range",
        "jobs",
        "max_attempts BETWEEN 1 AND 100",
    )
    op.create_index(
        "ix_jobs_status_available_at",
        "jobs",
        ["status", "available_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove retry scheduling fields in reverse dependency order."""

    op.drop_index(
        "ix_jobs_status_available_at",
        table_name="jobs",
    )
    op.drop_constraint(
        "ck_jobs_max_attempts_range",
        "jobs",
        type_="check",
    )
    op.drop_column("jobs", "available_at")
    op.drop_column("jobs", "max_attempts")
