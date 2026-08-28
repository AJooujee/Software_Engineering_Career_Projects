from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.database import SessionLocal
from app.main import app
from app.models import Warehouse


client = TestClient(app)


def test_warehouse_crud_and_soft_delete() -> None:
    """Verify the complete warehouse lifecycle and inactive filtering."""
    warehouse_code = f"TEST-{uuid4().hex[:8].upper()}"
    warehouse_id: str | None = None

    create_payload = {
        "code": warehouse_code.lower(),
        "name": "Automated Test Warehouse",
        "address_line_1": "500 Test Avenue",
        "address_line_2": None,
        "city": "Lowell",
        "state": "Massachusetts",
        "postal_code": "01852",
        "country_code": "us",
    }

    try:
        # Creating a warehouse normalizes business and country codes.
        create_response = client.post(
            "/warehouses",
            json=create_payload,
        )

        assert create_response.status_code == 201

        created_warehouse = create_response.json()
        warehouse_id = created_warehouse["id"]

        assert created_warehouse["code"] == warehouse_code
        assert created_warehouse["country_code"] == "US"
        assert created_warehouse["is_active"] is True

        # Codes are case-normalized, so a lowercase duplicate still conflicts.
        duplicate_response = client.post(
            "/warehouses",
            json=create_payload,
        )

        assert duplicate_response.status_code == 409
        assert duplicate_response.json()["detail"] == (
            f"Warehouse code '{warehouse_code}' already exists"
        )

        get_response = client.get(
            f"/warehouses/{warehouse_id}",
        )

        assert get_response.status_code == 200
        assert get_response.json()["id"] == warehouse_id

        # PATCH changes only explicitly supplied fields.
        update_response = client.patch(
            f"/warehouses/{warehouse_id}",
            json={
                "name": "Updated Automated Warehouse",
                "address_line_2": "Test Receiving Dock",
            },
        )

        assert update_response.status_code == 200

        updated_warehouse = update_response.json()

        assert updated_warehouse["name"] == (
            "Updated Automated Warehouse"
        )
        assert updated_warehouse["address_line_2"] == (
            "Test Receiving Dock"
        )
        assert updated_warehouse["city"] == "Lowell"

        active_list_response = client.get(
            "/warehouses",
            params={
                "include_inactive": False,
                "offset": 0,
                "limit": 100,
            },
        )

        assert active_list_response.status_code == 200
        assert any(
            warehouse["id"] == warehouse_id
            for warehouse in active_list_response.json()
        )

        # DELETE performs a soft delete to preserve historical references.
        delete_response = client.delete(
            f"/warehouses/{warehouse_id}",
        )

        assert delete_response.status_code == 204
        assert delete_response.content == b""

        active_after_delete_response = client.get(
            "/warehouses",
            params={
                "include_inactive": False,
                "offset": 0,
                "limit": 100,
            },
        )

        assert all(
            warehouse["id"] != warehouse_id
            for warehouse in active_after_delete_response.json()
        )

        historical_list_response = client.get(
            "/warehouses",
            params={
                "include_inactive": True,
                "offset": 0,
                "limit": 100,
            },
        )

        historical_warehouse = next(
            warehouse
            for warehouse in historical_list_response.json()
            if warehouse["id"] == warehouse_id
        )

        assert historical_warehouse["is_active"] is False

    finally:
        # Remove only the temporary record created by this automated test.
        if warehouse_id is not None:
            with SessionLocal() as database:
                database.execute(
                    delete(Warehouse).where(
                        Warehouse.id == UUID(warehouse_id),
                    )
                )
                database.commit()


def test_get_missing_warehouse_returns_404() -> None:
    """Return a clear HTTP response when a warehouse does not exist."""
    missing_warehouse_id = uuid4()

    response = client.get(
        f"/warehouses/{missing_warehouse_id}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        f"Warehouse '{missing_warehouse_id}' was not found"
    )