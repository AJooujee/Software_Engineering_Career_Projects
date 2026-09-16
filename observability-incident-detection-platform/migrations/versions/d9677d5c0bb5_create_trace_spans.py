"""Create persistent storage for distributed trace spans.

Revision ID: d9677d5c0bb5
Revises: e819fb574bb1
Create Date: 2026-09-16 15:07:19.125395
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic uses these identifiers to maintain the linear migration history.
revision: str = "d9677d5c0bb5"
down_revision: str | Sequence[str] | None = "e819fb574bb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create persistent storage and query indexes for trace spans."""

    # Create the parent trace span table before adding its query indexes.
    op.create_table(
        "trace_spans",
        # Use an internal UUID primary key independently of W3C identifiers.
        sa.Column("id", sa.Uuid(), nullable=False),
        # Associate each span with one registered monitored service.
        sa.Column("service_id", sa.Uuid(), nullable=False),
        # Preserve external identifiers used to reconstruct the trace graph.
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("span_id", sa.String(length=16), nullable=False),
        # Root spans have no parent, and parent spans may arrive later.
        sa.Column(
            "parent_span_id",
            sa.String(length=16),
            nullable=True,
        ),
        # Store runtime origin and the operation represented by the span.
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("operation", sa.String(length=200), nullable=False),
        # Store the normalized span result used by error queries.
        sa.Column("status", sa.String(length=20), nullable=False),
        # Preserve execution timing and precomputed latency.
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        # Preserve instrumentation-specific context without schema expansion.
        sa.Column("attributes", sa.JSON(), nullable=False),
        # Track platform receipt independently from span execution time.
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Delete spans automatically when their monitored service is removed.
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["monitored_services.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Prevent duplicate span identities within one distributed trace.
        sa.UniqueConstraint(
            "trace_id",
            "span_id",
            name="uq_trace_spans_trace_id_span_id",
        ),
    )

    # Support service-level latency queries over chronological time ranges.
    op.create_index(
        "ix_trace_span_service_started_at",
        "trace_spans",
        ["service_id", "started_at"],
        unique=False,
    )

    # Support status and error-rate queries over chronological time ranges.
    op.create_index(
        "ix_trace_span_status_started_at",
        "trace_spans",
        ["status", "started_at"],
        unique=False,
    )

    # Support chronological reconstruction of one complete trace.
    op.create_index(
        "ix_trace_span_trace_started_at",
        "trace_spans",
        ["trace_id", "started_at"],
        unique=False,
    )

    # Support efficient lookup of children belonging to a parent span.
    op.create_index(
        op.f("ix_trace_spans_parent_span_id"),
        "trace_spans",
        ["parent_span_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove trace span indexes and persistent storage."""

    # Drop dependent indexes before removing their underlying table.
    op.drop_index(
        op.f("ix_trace_spans_parent_span_id"),
        table_name="trace_spans",
    )
    op.drop_index(
        "ix_trace_span_trace_started_at",
        table_name="trace_spans",
    )
    op.drop_index(
        "ix_trace_span_status_started_at",
        table_name="trace_spans",
    )
    op.drop_index(
        "ix_trace_span_service_started_at",
        table_name="trace_spans",
    )

    # Removing the table also removes its primary, foreign, and unique
    # constraints.
    op.drop_table("trace_spans")
