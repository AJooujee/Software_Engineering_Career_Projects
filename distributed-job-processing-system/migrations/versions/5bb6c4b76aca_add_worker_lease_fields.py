"""Add worker lease and heartbeat fields.

Revision ID: 5bb6c4b76aca
Revises: b5f3b0955c95
Create Date: 2026-09-12 19:19:58.061073
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic uses these identifiers to determine migration order.
revision: str = "5bb6c4b76aca"
down_revision: str | Sequence[str] | None = "b5f3b0955c95"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add worker lease timestamps and an index for stale-job recovery."""

    op.add_column(
        "jobs",
        sa.Column(
            "lease_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "heartbeat_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_jobs_status_lease_expires_at",
        "jobs",
        ["status", "lease_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove worker lease fields in reverse dependency order."""

    op.drop_index(
        "ix_jobs_status_lease_expires_at",
        table_name="jobs",
    )
    op.drop_column("jobs", "heartbeat_at")
    op.drop_column("jobs", "lease_expires_at")
