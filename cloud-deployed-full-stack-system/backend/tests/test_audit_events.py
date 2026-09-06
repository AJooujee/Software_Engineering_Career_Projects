"""Integration tests for immutable administrator audit history."""

import json
from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import UserRole


def incident_payload(
    *,
    title: str = "Customer API outage",
    description: str = "Customer requests are returning errors.",
) -> dict[str, str]:
    """Return a valid Incident payload for audit test setup."""

    return {
        "title": title,
        "description": description,
        "service_name": "customer-api",
        "severity": "critical",
    }


def test_audit_history_is_restricted_to_administrators(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Require authentication and an administrator role for audit history."""

    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )
    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )
    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )

    unauthenticated_response = client.get(
        "/api/audit-events",
    )
    viewer_response = client.get(
        "/api/audit-events",
        headers=viewer["headers"],
    )
    operator_response = client.get(
        "/api/audit-events",
        headers=operator["headers"],
    )
    administrator_response = client.get(
        "/api/audit-events",
        headers=administrator["headers"],
    )

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json() == {
        "detail": "Not authenticated"
    }

    assert viewer_response.status_code == 403
    assert operator_response.status_code == 403

    assert viewer_response.json() == {
        "detail": "Insufficient permissions."
    }
    assert operator_response.json() == {
        "detail": "Insufficient permissions."
    }

    assert administrator_response.status_code == 200
    assert administrator_response.json() == []


def test_successful_mutations_create_safe_audit_events(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Record Incident and user mutations without storing secrets."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
        email="audit.admin@example.com",
    )
    target_user = authenticated_user_factory(
        role=UserRole.VIEWER,
        email="audit.target@example.com",
    )

    initial_description = (
        "Customer requests are returning errors."
    )
    updated_description = (
        "The operations team is investigating upstream failures."
    )

    create_response = client.post(
        "/api/incidents",
        headers=administrator["headers"],
        json=incident_payload(
            description=initial_description,
        ),
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/incidents/{incident_id}",
        headers=administrator["headers"],
        json={
            "description": updated_description,
            "status": "investigating",
        },
    )
    role_response = client.patch(
        f"/api/users/{target_user['id']}/role",
        headers=administrator["headers"],
        json={"role": "operator"},
    )
    status_response = client.patch(
        f"/api/users/{target_user['id']}/status",
        headers=administrator["headers"],
        json={"is_active": False},
    )
    delete_response = client.delete(
        f"/api/incidents/{incident_id}",
        headers=administrator["headers"],
    )

    assert update_response.status_code == 200
    assert role_response.status_code == 200
    assert status_response.status_code == 200
    assert delete_response.status_code == 204

    history_response = client.get(
        "/api/audit-events",
        headers=administrator["headers"],
    )

    assert history_response.status_code == 200

    events = history_response.json()
    actions = [
        event["action"]
        for event in events
    ]

    # Audit history is returned newest first for direct dashboard use.
    assert actions == [
        "incident.deleted",
        "user.status_changed",
        "user.role_changed",
        "incident.updated",
        "incident.created",
    ]

    events_by_action = {
        event["action"]: event
        for event in events
    }

    created_event = events_by_action["incident.created"]
    updated_event = events_by_action["incident.updated"]
    deleted_event = events_by_action["incident.deleted"]
    role_event = events_by_action["user.role_changed"]
    status_event = events_by_action["user.status_changed"]

    # Actor fields are immutable snapshots of who performed the action.
    assert all(
        event["actor_user_id"] == administrator["id"]
        for event in events
    )
    assert all(
        event["actor_email"] == administrator["email"]
        for event in events
    )
    assert all(
        event["actor_role"] == "admin"
        for event in events
    )

    assert created_event["resource_type"] == "incident"
    assert created_event["resource_id"] == incident_id
    assert created_event["resource_label"] == (
        "Customer API outage"
    )
    assert created_event["changes"]["severity"] == {
        "from": None,
        "to": "critical",
    }
    assert created_event["changes"]["status"] == {
        "from": None,
        "to": "open",
    }

    assert updated_event["changes"] == {
        "description": {
            "from": initial_description,
            "to": updated_description,
        },
        "status": {
            "from": "open",
            "to": "investigating",
        },
    }

    assert deleted_event["resource_id"] == incident_id
    assert deleted_event["resource_label"] == (
        "Customer API outage"
    )
    assert deleted_event["changes"] == {
        "deleted": {
            "from": False,
            "to": True,
        }
    }

    assert role_event["resource_type"] == "user"
    assert role_event["resource_id"] == target_user["id"]
    assert role_event["resource_label"] == target_user["email"]
    assert role_event["changes"] == {
        "role": {
            "from": "viewer",
            "to": "operator",
        }
    }

    assert status_event["resource_type"] == "user"
    assert status_event["resource_id"] == target_user["id"]
    assert status_event["changes"] == {
        "is_active": {
            "from": True,
            "to": False,
        }
    }

    serialized_history = json.dumps(events).lower()

    # Audit payloads must never expose authentication secrets.
    assert "password" not in serialized_history
    assert "token" not in serialized_history


def test_failed_and_unchanged_mutations_are_not_audited(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Exclude rejected requests and no-op updates from audit history."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )
    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )

    forbidden_create_response = client.post(
        "/api/incidents",
        headers=viewer["headers"],
        json=incident_payload(
            title="Unauthorized Incident",
        ),
    )
    rejected_demotion_response = client.patch(
        f"/api/users/{administrator['id']}/role",
        headers=administrator["headers"],
        json={"role": "viewer"},
    )

    assert forbidden_create_response.status_code == 403
    assert rejected_demotion_response.status_code == 400

    create_response = client.post(
        "/api/incidents",
        headers=administrator["headers"],
        json=incident_payload(
            title="Stable Incident",
        ),
    )

    assert create_response.status_code == 201

    incident = create_response.json()

    # Supplying existing values is successful but does not describe a change.
    unchanged_response = client.patch(
        f"/api/incidents/{incident['id']}",
        headers=administrator["headers"],
        json={
            "title": incident["title"],
            "status": incident["status"],
        },
    )

    assert unchanged_response.status_code == 200

    history_response = client.get(
        "/api/audit-events",
        headers=administrator["headers"],
    )

    assert history_response.status_code == 200
    assert [
        event["action"]
        for event in history_response.json()
    ] == ["incident.created"]
