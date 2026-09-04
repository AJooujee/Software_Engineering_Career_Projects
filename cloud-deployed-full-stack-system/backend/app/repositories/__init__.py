"""Repository functions used to access persisted incident data."""

from app.repositories.incidents import (
    create_incident,
    delete_incident,
    get_incident,
    list_incidents,
    update_incident,
)


__all__ = [
    "create_incident",
    "delete_incident",
    "get_incident",
    "list_incidents",
    "update_incident",
]

from app.repositories.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user_role,
    update_user_status,
)
