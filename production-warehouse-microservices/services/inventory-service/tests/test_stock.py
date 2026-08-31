from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.database import SessionLocal
from app.main import app
from app.models import InventoryBalance, Product, StockMovement


client = TestClient(app)


def test_stock_receipt_issue_and_insufficient_stock() -> None:
    warehouse_id = "22222222-2222-4222-8222-222222222222"
    sku = f"TEST-{uuid4().hex[:8].upper()}"
    product_id: str | None = None

    try:
        # Create a unique product for this test.
        create_product_response = client.post(
            "/products",
            json={
                "sku": sku,
                "name": "Automated Test Product",
                "description": "Temporary product used by stock API tests.",
                "unit_price": 99.99,
                "reorder_level": 5,
            },
        )

        assert create_product_response.status_code == 201

        product_id = create_product_response.json()["id"]

        # Receive 100 units.
        receipt_response = client.post(
            "/stock/receipts",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 100,
                "reference_id": "TEST-PO-001",
                "reason": "Automated stock receipt test",
            },
        )

        assert receipt_response.status_code == 201

        receipt_body = receipt_response.json()

        assert receipt_body["balance"]["quantity_on_hand"] == 100
        assert receipt_body["balance"]["quantity_reserved"] == 0
        assert receipt_body["balance"]["available_quantity"] == 100
        assert receipt_body["movement"]["movement_type"] == "RECEIPT"
        assert receipt_body["movement"]["on_hand_delta"] == 100
        assert receipt_body["movement"]["on_hand_balance_after"] == 100

        # Issue 30 units.
        issue_response = client.post(
            "/stock/issues",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 30,
                "reference_id": "TEST-SO-001",
                "reason": "Automated stock issue test",
            },
        )

        assert issue_response.status_code == 200

        issue_body = issue_response.json()

        assert issue_body["balance"]["quantity_on_hand"] == 70
        assert issue_body["balance"]["available_quantity"] == 70
        assert issue_body["movement"]["movement_type"] == "ISSUE"
        assert issue_body["movement"]["on_hand_delta"] == -30
        assert issue_body["movement"]["on_hand_balance_after"] == 70

        # Attempt to issue more than the available stock.
        rejected_response = client.post(
            "/stock/issues",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 100,
                "reference_id": "TEST-SO-002",
                "reason": "Automated insufficient stock test",
            },
        )

        assert rejected_response.status_code == 409

        rejected_detail = rejected_response.json()["detail"]

        assert rejected_detail["available_quantity"] == 70
        assert rejected_detail["requested_quantity"] == 100

        # Confirm the failed issue did not change the balance.
        balance_response = client.get(
            f"/stock/balances/{warehouse_id}/{product_id}",
        )

        assert balance_response.status_code == 200
        assert balance_response.json()["quantity_on_hand"] == 70
        assert balance_response.json()["available_quantity"] == 70

        # Confirm only successful movements were recorded.
        movements_response = client.get(
            "/stock/movements",
            params={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "offset": 0,
                "limit": 100,
            },
        )

        assert movements_response.status_code == 200

        movements = movements_response.json()

        assert len(movements) == 2
        assert {movement["movement_type"] for movement in movements} == {
            "RECEIPT",
            "ISSUE",
        }
        assert all(
            movement["on_hand_delta"] != -100
            for movement in movements
        )

    finally:
        # Remove all temporary test records.
        if product_id is not None:
            product_uuid = UUID(product_id)
            warehouse_uuid = UUID(warehouse_id)

            with SessionLocal() as database:
                database.execute(
                    delete(StockMovement).where(
                        StockMovement.product_id == product_uuid,
                        StockMovement.warehouse_id == warehouse_uuid,
                    )
                )
                database.execute(
                    delete(InventoryBalance).where(
                        InventoryBalance.product_id == product_uuid,
                        InventoryBalance.warehouse_id == warehouse_uuid,
                    )
                )
                database.execute(
                    delete(Product).where(
                        Product.id == product_uuid,
                    )
                )
                database.commit()

def test_stock_transfer_is_atomic() -> None:
    """Verify successful, rejected, and invalid stock transfers."""

    source_warehouse_id = "33333333-3333-4333-8333-333333333333"
    destination_warehouse_id = "44444444-4444-4444-8444-444444444444"
    sku = f"TRANSFER-{uuid4().hex[:8].upper()}"
    product_id: str | None = None

    try:
        # Create a product owned only by this test.
        create_product_response = client.post(
            "/products",
            json={
                "sku": sku,
                "name": "Stock Transfer Test Product",
                "description": "Temporary product used by transfer tests.",
                "unit_price": 149.99,
                "reorder_level": 10,
            },
        )

        assert create_product_response.status_code == 201

        product_id = create_product_response.json()["id"]

        # Seed only the source warehouse with inventory.
        receipt_response = client.post(
            "/stock/receipts",
            json={
                "product_id": product_id,
                "warehouse_id": source_warehouse_id,
                "quantity": 100,
                "reference_id": "TRANSFER-RECEIPT-001",
                "reason": "Seed source warehouse for transfer test",
            },
        )

        assert receipt_response.status_code == 201

        # Transfer 40 units from the source to the destination.
        transfer_response = client.post(
            "/stock/transfers",
            json={
                "product_id": product_id,
                "source_warehouse_id": source_warehouse_id,
                "destination_warehouse_id": destination_warehouse_id,
                "quantity": 40,
                "reference_id": "TRANSFER-001",
                "reason": "Automated warehouse transfer test",
            },
        )

        assert transfer_response.status_code == 200

        transfer_body = transfer_response.json()
        transfer_id = transfer_body["transfer_id"]

        assert transfer_body["source_balance"]["quantity_on_hand"] == 60
        assert transfer_body["source_balance"]["available_quantity"] == 60
        assert (
            transfer_body["destination_balance"]["quantity_on_hand"]
            == 40
        )
        assert (
            transfer_body["destination_balance"]["available_quantity"]
            == 40
        )

        outbound = transfer_body["outbound_movement"]
        inbound = transfer_body["inbound_movement"]

        assert outbound["movement_type"] == "TRANSFER_OUT"
        assert outbound["on_hand_delta"] == -40
        assert outbound["on_hand_balance_after"] == 60
        assert outbound["transfer_id"] == transfer_id

        assert inbound["movement_type"] == "TRANSFER_IN"
        assert inbound["on_hand_delta"] == 40
        assert inbound["on_hand_balance_after"] == 40
        assert inbound["transfer_id"] == transfer_id

        # Querying by transfer ID must return the paired audit records.
        movements_response = client.get(
            "/stock/movements",
            params={
                "transfer_id": transfer_id,
                "offset": 0,
                "limit": 100,
            },
        )

        assert movements_response.status_code == 200

        transfer_movements = movements_response.json()

        assert len(transfer_movements) == 2
        assert {
            movement["movement_type"]
            for movement in transfer_movements
        } == {
            "TRANSFER_OUT",
            "TRANSFER_IN",
        }
        assert all(
            movement["transfer_id"] == transfer_id
            for movement in transfer_movements
        )

        # Attempting to transfer more than the available source stock
        # must roll back the destination balance and movement records.
        rejected_response = client.post(
            "/stock/transfers",
            json={
                "product_id": product_id,
                "source_warehouse_id": source_warehouse_id,
                "destination_warehouse_id": destination_warehouse_id,
                "quantity": 100,
                "reference_id": "TRANSFER-002",
                "reason": "Automated insufficient transfer test",
            },
        )

        assert rejected_response.status_code == 409

        rejected_detail = rejected_response.json()["detail"]

        assert rejected_detail["available_quantity"] == 60
        assert rejected_detail["requested_quantity"] == 100

        # Both balances must remain unchanged after the rejected transfer.
        source_balance_response = client.get(
            f"/stock/balances/{source_warehouse_id}/{product_id}",
        )
        destination_balance_response = client.get(
            f"/stock/balances/{destination_warehouse_id}/{product_id}",
        )

        assert source_balance_response.status_code == 200
        assert destination_balance_response.status_code == 200
        assert source_balance_response.json()["quantity_on_hand"] == 60
        assert destination_balance_response.json()["quantity_on_hand"] == 40

        # Pydantic rejects transfers whose source and destination match
        # before the business transaction begins.
        same_warehouse_response = client.post(
            "/stock/transfers",
            json={
                "product_id": product_id,
                "source_warehouse_id": source_warehouse_id,
                "destination_warehouse_id": source_warehouse_id,
                "quantity": 10,
                "reference_id": "TRANSFER-003",
                "reason": "Invalid same-warehouse transfer test",
            },
        )

        assert same_warehouse_response.status_code == 422

        # The failed transfer must not create additional paired movements.
        movements_after_rejection = client.get(
            "/stock/movements",
            params={
                "product_id": product_id,
                "offset": 0,
                "limit": 100,
            },
        )

        assert movements_after_rejection.status_code == 200
        assert len(movements_after_rejection.json()) == 3

    finally:
        # Remove movements and balances from both warehouses before
        # deleting the temporary product.
        if product_id is not None:
            product_uuid = UUID(product_id)

            with SessionLocal() as database:
                database.execute(
                    delete(StockMovement).where(
                        StockMovement.product_id == product_uuid,
                    )
                )
                database.execute(
                    delete(InventoryBalance).where(
                        InventoryBalance.product_id == product_uuid,
                    )
                )
                database.execute(
                    delete(Product).where(
                        Product.id == product_uuid,
                    )
                )
                database.commit()

def test_stock_reservation_and_release_are_order_scoped() -> None:
    """Verify reservation ownership, validation, and rollback behavior."""

    warehouse_id = "55555555-5555-4555-8555-555555555555"
    order_reference = f"ORDER-{uuid4().hex[:12].upper()}"
    other_reference = f"ORDER-{uuid4().hex[:12].upper()}"
    sku = f"RESERVE-{uuid4().hex[:8].upper()}"
    product_id: str | None = None

    try:
        # Create a product owned only by this test.
        create_product_response = client.post(
            "/products",
            json={
                "sku": sku,
                "name": "Reservation Test Product",
                "description": "Temporary product for reservation tests.",
                "unit_price": 79.99,
                "reorder_level": 5,
            },
        )

        assert create_product_response.status_code == 201

        product_id = create_product_response.json()["id"]

        # Seed the warehouse with 100 available units.
        receipt_response = client.post(
            "/stock/receipts",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 100,
                "reference_id": "RESERVATION-RECEIPT-001",
                "reason": "Seed stock for reservation test",
            },
        )

        assert receipt_response.status_code == 201

        # Reserve 30 units for one order.
        reservation_response = client.post(
            "/stock/reservations",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 30,
                "reference_id": order_reference,
                "reason": "Reserve inventory for automated order",
            },
        )

        assert reservation_response.status_code == 200

        reservation_body = reservation_response.json()

        assert reservation_body["balance"]["quantity_on_hand"] == 100
        assert reservation_body["balance"]["quantity_reserved"] == 30
        assert reservation_body["balance"]["available_quantity"] == 70
        assert (
            reservation_body["movement"]["movement_type"]
            == "RESERVATION"
        )
        assert reservation_body["movement"]["on_hand_delta"] == 0
        assert reservation_body["movement"]["reserved_delta"] == 30

        # Retrying the same order reference must not reserve stock twice.
        duplicate_response = client.post(
            "/stock/reservations",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 30,
                "reference_id": order_reference,
                "reason": "Duplicate reservation retry",
            },
        )

        assert duplicate_response.status_code == 409
        assert (
            duplicate_response.json()["detail"]["reserved_quantity"]
            == 30
        )

        # A different order cannot reserve above the remaining availability.
        insufficient_response = client.post(
            "/stock/reservations",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 80,
                "reference_id": other_reference,
                "reason": "Insufficient reservation test",
            },
        )

        assert insufficient_response.status_code == 409
        assert (
            insufficient_response.json()["detail"]["available_quantity"]
            == 70
        )

        # Another order reference cannot release this order's reservation.
        wrong_reference_response = client.post(
            "/stock/releases",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 5,
                "reference_id": other_reference,
                "reason": "Attempt to release another order's stock",
            },
        )

        assert wrong_reference_response.status_code == 409
        assert (
            wrong_reference_response.json()["detail"][
                "reserved_quantity"
            ]
            == 0
        )

        # Partially release 10 units from the owning order.
        partial_release_response = client.post(
            "/stock/releases",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 10,
                "reference_id": order_reference,
                "reason": "Partial order cancellation",
            },
        )

        assert partial_release_response.status_code == 200

        partial_release_body = partial_release_response.json()

        assert partial_release_body["balance"]["quantity_on_hand"] == 100
        assert partial_release_body["balance"]["quantity_reserved"] == 20
        assert partial_release_body["balance"]["available_quantity"] == 80
        assert (
            partial_release_body["movement"]["movement_type"]
            == "RELEASE"
        )
        assert partial_release_body["movement"]["reserved_delta"] == -10

        # Releasing above the order's remaining reservation must roll back.
        excessive_release_response = client.post(
            "/stock/releases",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 25,
                "reference_id": order_reference,
                "reason": "Excessive release test",
            },
        )

        assert excessive_release_response.status_code == 409

        excessive_detail = excessive_release_response.json()["detail"]

        assert excessive_detail["reserved_quantity"] == 20
        assert excessive_detail["requested_quantity"] == 25

        # Release the final 20 units owned by the order.
        final_release_response = client.post(
            "/stock/releases",
            json={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 20,
                "reference_id": order_reference,
                "reason": "Release remaining order reservation",
            },
        )

        assert final_release_response.status_code == 200

        final_balance = final_release_response.json()["balance"]

        assert final_balance["quantity_on_hand"] == 100
        assert final_balance["quantity_reserved"] == 0
        assert final_balance["available_quantity"] == 100

        # Only successful operations should appear in movement history.
        movements_response = client.get(
            "/stock/movements",
            params={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "offset": 0,
                "limit": 100,
            },
        )

        assert movements_response.status_code == 200

        movements = movements_response.json()

        assert len(movements) == 4
        assert [
            movement["movement_type"]
            for movement in movements
        ].count("RESERVATION") == 1
        assert [
            movement["movement_type"]
            for movement in movements
        ].count("RELEASE") == 2

    finally:
        # Remove every temporary movement and balance before the product.
        if product_id is not None:
            product_uuid = UUID(product_id)

            with SessionLocal() as database:
                database.execute(
                    delete(StockMovement).where(
                        StockMovement.product_id == product_uuid,
                    )
                )
                database.execute(
                    delete(InventoryBalance).where(
                        InventoryBalance.product_id == product_uuid,
                    )
                )
                database.execute(
                    delete(Product).where(
                        Product.id == product_uuid,
                    )
                )
                database.commit()