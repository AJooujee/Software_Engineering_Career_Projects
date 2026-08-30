"""Add stock transfer movement tracking.

Revision ID: be8514c2d2b9
Revises: db993ddf412b
Create Date: 2026-08-28 18:54:52.801779
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers.
revision: str = "be8514c2d2b9"
down_revision: Union[str, Sequence[str], None] = "db993ddf412b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transfer tracking and allow transfer movement types."""

    # Both sides of one transfer share this ID, allowing the outbound and
    # inbound audit records to be queried as one business operation.
    op.add_column(
        "stock_movements",
        sa.Column(
            "transfer_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_stock_movements_transfer_id"),
        "stock_movements",
        ["transfer_id"],
        unique=False,
    )

    # Alembic does not automatically detect changes inside an existing
    # named check constraint, so the movement rule must be replaced.
    op.drop_constraint(
        "ck_stock_movements_valid_type",
        "stock_movements",
        type_="check",
    )
    op.create_check_constraint(
        "ck_stock_movements_valid_type",
        "stock_movements",
        """
        movement_type IN (
            'RECEIPT',
            'ISSUE',
            'ADJUSTMENT',
            'RESERVATION',
            'RELEASE',
            'TRANSFER_OUT',
            'TRANSFER_IN'
        )
        """,
    )


def downgrade() -> None:
    """Remove transfer tracking and restore the previous movement types."""

    # This downgrade expects that no transfer movement records remain.
    # PostgreSQL will reject the old constraint if transfer data exists.
    op.drop_constraint(
        "ck_stock_movements_valid_type",
        "stock_movements",
        type_="check",
    )
    op.create_check_constraint(
        "ck_stock_movements_valid_type",
        "stock_movements",
        """
        movement_type IN (
            'RECEIPT',
            'ISSUE',
            'ADJUSTMENT',
            'RESERVATION',
            'RELEASE'
        )
        """,
    )

    op.drop_index(
        op.f("ix_stock_movements_transfer_id"),
        table_name="stock_movements",
    )
    op.drop_column(
        "stock_movements",
        "transfer_id",
    )