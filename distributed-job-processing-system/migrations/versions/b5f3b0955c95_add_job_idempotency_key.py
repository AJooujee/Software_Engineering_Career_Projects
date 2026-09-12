"""Add a unique idempotency key to jobs.

Revision ID: b5f3b0955c95
Revises: f233f5d3a0fd
Create Date: 2026-09-12 18:04:55.380569
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic uses these identifiers to determine migration order.
revision: str = "b5f3b0955c95"
down_revision: str | Sequence[str] | None = "f233f5d3a0fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add an optional globally unique idempotency key to jobs."""

    # PostgreSQL permits multiple NULL values in a unique constraint, allowing
    # clients to continue submitting jobs without an idempotency key.
    op.add_column(
        "jobs",
        sa.Column(
            "idempotency_key",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_jobs_idempotency_key",
        "jobs",
        ["idempotency_key"],
    )


def downgrade() -> None:
    """Remove the idempotency constraint and column."""

    op.drop_constraint(
        "uq_jobs_idempotency_key",
        "jobs",
        type_="unique",
    )
    op.drop_column("jobs", "idempotency_key")
