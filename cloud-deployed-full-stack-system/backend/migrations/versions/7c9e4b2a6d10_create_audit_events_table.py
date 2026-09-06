"""create audit events table

Revision ID: 7c9e4b2a6d10
Revises: 6b0140f7a01f
Create Date: 2026-09-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c9e4b2a6d10"
down_revision: Union[str, Sequence[str], None] = "6b0140f7a01f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create immutable audit-event persistence."""

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "actor_email",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "actor_role",
            sa.Enum(
                "viewer",
                "operator",
                "admin",
                name="audit_actor_role",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "incident.created",
                "incident.updated",
                "incident.deleted",
                "user.role_changed",
                "user.status_changed",
                name="audit_action",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "resource_type",
            sa.Enum(
                "incident",
                "user",
                name="audit_resource_type",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "resource_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "resource_label",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "changes",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "actor_role IN ('viewer', 'operator', 'admin')",
            name="audit_actor_role",
        ),
        sa.CheckConstraint(
            (
                "action IN ("
                "'incident.created', "
                "'incident.updated', "
                "'incident.deleted', "
                "'user.role_changed', "
                "'user.status_changed'"
                ")"
            ),
            name="audit_action",
        ),
        sa.CheckConstraint(
            "resource_type IN ('incident', 'user')",
            name="audit_resource_type",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f(
                "fk_audit_events_actor_user_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_audit_events"),
        ),
    )

    op.create_index(
        op.f("ix_audit_events_action"),
        "audit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_actor_user_id"),
        "audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_created_at"),
        "audit_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_resource_id"),
        "audit_events",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_resource_type"),
        "audit_events",
        ["resource_type"],
        unique=False,
    )


def downgrade() -> None:
    """Remove audit-event persistence."""

    op.drop_index(
        op.f("ix_audit_events_resource_type"),
        table_name="audit_events",
    )
    op.drop_index(
        op.f("ix_audit_events_resource_id"),
        table_name="audit_events",
    )
    op.drop_index(
        op.f("ix_audit_events_created_at"),
        table_name="audit_events",
    )
    op.drop_index(
        op.f("ix_audit_events_actor_user_id"),
        table_name="audit_events",
    )
    op.drop_index(
        op.f("ix_audit_events_action"),
        table_name="audit_events",
    )
    op.drop_table("audit_events")
