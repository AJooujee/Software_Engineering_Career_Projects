"""Integration tests for administrator user-management authorization."""

from collections.abc import Callable
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.user import UserRole


def test_viewer_cannot_access_user_administration(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Prevent viewers from listing users or promoting themselves."""

    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )

    list_response = client.get(
        "/api/users",
        headers=viewer["headers"],
    )

    promotion_response = client.patch(
        f"/api/users/{viewer['id']}/role",
        headers=viewer["headers"],
        json={"role": "admin"},
    )

    assert list_response.status_code == 403
    assert promotion_response.status_code == 403

    assert list_response.json() == {
        "detail": "Insufficient permissions."
    }
    assert promotion_response.json() == {
        "detail": "Insufficient permissions."
    }


def test_admin_can_manage_users_and_roles_apply_immediately(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Apply database role and status changes to existing tokens."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )
    target_user = authenticated_user_factory(
        role=UserRole.VIEWER,
    )

    list_response = client.get(
        "/api/users",
        headers=administrator["headers"],
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 2
    assert all(
        "password_hash" not in user
        for user in list_response.json()
    )

    role_response = client.patch(
        f"/api/users/{target_user['id']}/role",
        headers=administrator["headers"],
        json={"role": "operator"},
    )

    assert role_response.status_code == 200
    assert role_response.json()["role"] == "operator"

    # The existing target token now receives operator permissions.
    create_incident_response = client.post(
        "/api/incidents",
        headers=target_user["headers"],
        json={
            "title": "Database latency",
            "description": "Queries exceed the latency threshold.",
            "service_name": "database-api",
            "severity": "high",
        },
    )

    assert create_incident_response.status_code == 201

    status_response = client.patch(
        f"/api/users/{target_user['id']}/status",
        headers=administrator["headers"],
        json={"is_active": False},
    )

    assert status_response.status_code == 200
    assert status_response.json()["is_active"] is False

    # The same token is rejected after the account is disabled.
    disabled_token_response = client.get(
        "/api/auth/me",
        headers=target_user["headers"],
    )

    assert disabled_token_response.status_code == 403
    assert disabled_token_response.json() == {
        "detail": "User account is disabled."
    }


def test_admin_cannot_demote_or_disable_self(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Prevent an administrator from accidentally locking out self."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )

    demotion_response = client.patch(
        f"/api/users/{administrator['id']}/role",
        headers=administrator["headers"],
        json={"role": "viewer"},
    )

    disable_response = client.patch(
        f"/api/users/{administrator['id']}/status",
        headers=administrator["headers"],
        json={"is_active": False},
    )

    assert demotion_response.status_code == 400
    assert demotion_response.json() == {
        "detail": "Administrators cannot remove their own admin role."
    }

    assert disable_response.status_code == 400
    assert disable_response.json() == {
        "detail": "Administrators cannot disable their own account."
    }


def test_admin_receives_not_found_for_unknown_user(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Return a descriptive response for an unknown user identifier."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )
    missing_user_id = uuid4()

    response = client.get(
        f"/api/users/{missing_user_id}",
        headers=administrator["headers"],
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"User '{missing_user_id}' was not found."
    }
