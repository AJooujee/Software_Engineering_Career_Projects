from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint(
            """
            movement_type IN (
                'RECEIPT',
                'ISSUE',
                'ADJUSTMENT',
                'RESERVATION',
                'RELEASE'
            )
            """,
            name="ck_stock_movements_valid_type",
        ),
        CheckConstraint(
            "on_hand_delta <> 0 OR reserved_delta <> 0",
            name="ck_stock_movements_non_zero_delta",
        ),
        CheckConstraint(
            "on_hand_balance_after >= 0",
            name="ck_stock_movements_on_hand_after_non_negative",
        ),
        CheckConstraint(
            "reserved_balance_after >= 0",
            name="ck_stock_movements_reserved_after_non_negative",
        ),
        Index(
            "ix_stock_movements_product_warehouse_created",
            "product_id",
            "warehouse_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid,
        index=True,
        nullable=False,
    )
    movement_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    on_hand_delta: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    reserved_delta: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    on_hand_balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    reserved_balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )