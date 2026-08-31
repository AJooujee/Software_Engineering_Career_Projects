from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.api.routes.orders import get_service_client
from app.db.database import SessionLocal
from app.main import app
from app.models import Order
from app.services import (
    ProductSnapshot,
    ProductUnavailableError,
    StockReservationError,
)


client = TestClient(app)


class FakeServiceClient:
    """Controllable replacement for Inventory and Warehouse HTTP calls."""

    def __init__(
        self,
        prices: dict[UUID, Decimal],
        *,
        failed_reservation_product_id: UUID | None = None,
    ) -> None:
        self.prices = prices
        self.failed_reservation_product_id = (
            failed_reservation_product_id
        )
        self.reserved: list[tuple[UUID, UUID, int, str]] = []
        self.released: list[tuple[UUID, UUID, int, str]] = []

    def verify_warehouse(self, warehouse_id: UUID) -> None:
        """Treat the test warehouse as active."""

    def get_product(self, product_id: UUID) -> ProductSnapshot:
        """Return an authoritative test price for one product."""

        if product_id not in self.prices:
            raise ProductUnavailableError(
                f"Product '{product_id}' was not found"
            )

        return ProductSnapshot(
            product_id=product_id,
            unit_price=self.prices[product_id],
        )

    def reserve_stock(
        self,
        *,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: int,
        reference_id: str,
    ) -> None:
        """Record reservations or fail on the configured product."""

        if product_id == self.failed_reservation_product_id:
            raise StockReservationError(
                "Simulated insufficient stock"
            )

        self.reserved.append(
            (
                product_id,
                warehouse_id,
                quantity,
                reference_id,
            )
        )

    def release_stock(
        self,
        *,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: int,
        reference_id: str,
    ) -> None:
        """Record every reservation release."""

        self.released.append(
            (
                product_id,
                warehouse_id,
                quantity,
                reference_id,
            )
        )


@contextmanager
def _use_fake_service_client(
    fake_service_client: FakeServiceClient,
) -> Iterator[None]:
    """Temporarily replace the FastAPI downstream-client dependency."""

    app.dependency_overrides[get_service_client] = (
        lambda: fake_service_client
    )

    try:
        yield
    finally:
        app.dependency_overrides.pop(
            get_service_client,
            None,
        )


def _delete_orders_for_email(customer_email: str) -> None:
    """Remove test-owned orders; database cascade removes their items."""

    with SessionLocal() as database:
        database.execute(
            delete(Order).where(
                Order.customer_email == customer_email
            )
        )
        database.commit()


def test_order_create_read_list_and_cancel() -> None:
    """Verify reservation, calculated totals, reads, and cancellation."""

    warehouse_id = uuid4()
    first_product_id = uuid4()
    second_product_id = uuid4()
    customer_email = f"order-{uuid4().hex[:12]}@example.com"

    fake_service_client = FakeServiceClient(
        {
            first_product_id: Decimal("10.50"),
            second_product_id: Decimal("5.25"),
        }
    )

    try:
        with _use_fake_service_client(fake_service_client):
            create_response = client.post(
                "/orders",
                json={
                    "customer_name": "AJ Test Customer",
                    "customer_email": customer_email,
                    "warehouse_id": str(warehouse_id),
                    "items": [
                        {
                            "product_id": str(first_product_id),
                            "quantity": 2,
                        },
                        {
                            "product_id": str(second_product_id),
                            "quantity": 4,
                        },
                    ],
                },
            )

            assert create_response.status_code == 201

            created_order = create_response.json()
            order_id = created_order["id"]

            assert created_order["status"] == "RESERVED"
            assert Decimal(
                created_order["total_amount"]
            ) == Decimal("42.00")
            assert len(created_order["items"]) == 2
            assert len(fake_service_client.reserved) == 2

            item_totals = {
                item["product_id"]: Decimal(item["line_total"])
                for item in created_order["items"]
            }

            assert item_totals[str(first_product_id)] == Decimal(
                "21.00"
            )
            assert item_totals[str(second_product_id)] == Decimal(
                "21.00"
            )

            get_response = client.get(
                f"/orders/{order_id}"
            )

            assert get_response.status_code == 200
            assert get_response.json()["id"] == order_id

            list_response = client.get(
                "/orders",
                params={
                    "status": "RESERVED",
                    "offset": 0,
                    "limit": 100,
                },
            )

            assert list_response.status_code == 200
            assert order_id in {
                order["id"]
                for order in list_response.json()
            }

            cancel_response = client.post(
                f"/orders/{order_id}/cancel"
            )

            assert cancel_response.status_code == 200
            assert cancel_response.json()["status"] == "CANCELLED"
            assert len(fake_service_client.released) == 2

            # A cancellation retry must not release the same stock twice.
            second_cancel_response = client.post(
                f"/orders/{order_id}/cancel"
            )

            assert second_cancel_response.status_code == 200
            assert second_cancel_response.json()["status"] == "CANCELLED"
            assert len(fake_service_client.released) == 2

    finally:
        _delete_orders_for_email(customer_email)


def test_reserved_order_can_be_confirmed() -> None:
    """Verify the RESERVED-to-CONFIRMED lifecycle transition."""

    warehouse_id = uuid4()
    product_id = uuid4()
    customer_email = f"confirm-{uuid4().hex[:12]}@example.com"
    fake_service_client = FakeServiceClient(
        {
            product_id: Decimal("25.00"),
        }
    )

    try:
        with _use_fake_service_client(fake_service_client):
            create_response = client.post(
                "/orders",
                json={
                    "customer_name": "Confirmation Test Customer",
                    "customer_email": customer_email,
                    "warehouse_id": str(warehouse_id),
                    "items": [
                        {
                            "product_id": str(product_id),
                            "quantity": 1,
                        }
                    ],
                },
            )

            assert create_response.status_code == 201
            order_id = create_response.json()["id"]

            confirm_response = client.post(
                f"/orders/{order_id}/confirm"
            )

            assert confirm_response.status_code == 200
            assert confirm_response.json()["status"] == "CONFIRMED"

            # Confirmation is idempotent for safe client retries.
            second_confirm_response = client.post(
                f"/orders/{order_id}/confirm"
            )

            assert second_confirm_response.status_code == 200
            assert (
                second_confirm_response.json()["status"]
                == "CONFIRMED"
            )

            cancel_response = client.post(
                f"/orders/{order_id}/cancel"
            )

            assert cancel_response.status_code == 409
            assert fake_service_client.released == []

    finally:
        _delete_orders_for_email(customer_email)


def test_failed_reservation_compensates_successful_lines() -> None:
    """Verify partial reservations are released and no order is saved."""

    warehouse_id = uuid4()
    first_product_id = uuid4()
    failed_product_id = uuid4()
    customer_email = f"failed-{uuid4().hex[:12]}@example.com"

    fake_service_client = FakeServiceClient(
        {
            first_product_id: Decimal("12.00"),
            failed_product_id: Decimal("30.00"),
        },
        failed_reservation_product_id=failed_product_id,
    )

    try:
        with _use_fake_service_client(fake_service_client):
            response = client.post(
                "/orders",
                json={
                    "customer_name": "Compensation Test Customer",
                    "customer_email": customer_email,
                    "warehouse_id": str(warehouse_id),
                    "items": [
                        {
                            "product_id": str(first_product_id),
                            "quantity": 2,
                        },
                        {
                            "product_id": str(failed_product_id),
                            "quantity": 1,
                        },
                    ],
                },
            )

            assert response.status_code == 409

        # The first reservation succeeded and was then released.
        assert len(fake_service_client.reserved) == 1
        assert len(fake_service_client.released) == 1
        assert (
            fake_service_client.reserved[0]
            == fake_service_client.released[0]
        )

        # The local database transaction must also be rolled back.
        with SessionLocal() as database:
            saved_order_count = database.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.customer_email == customer_email)
            )

        assert saved_order_count == 0

    finally:
        _delete_orders_for_email(customer_email)


def test_get_missing_order_returns_404() -> None:
    """Verify that an unknown order ID returns a clear response."""

    response = client.get(
        f"/orders/{uuid4()}"
    )

    assert response.status_code == 404