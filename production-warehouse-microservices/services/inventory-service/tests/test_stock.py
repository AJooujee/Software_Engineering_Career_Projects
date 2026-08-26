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