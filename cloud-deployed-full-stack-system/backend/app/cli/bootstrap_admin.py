"""Create or promote the initial Cloud Operations administrator."""

import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.user import UserRole
import app.repositories.users as user_repository
from app.schemas.user import UserCreate
import app.services.auth as auth_service


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Create a new administrator or promote an existing user."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the administrator account.",
    )
    parser.add_argument(
        "--full-name",
        help="Full name required when creating a new account.",
    )

    return parser


def read_new_user_password() -> str:
    """Read and confirm a password without displaying it."""

    password = getpass("Administrator password: ")
    password_confirmation = getpass("Confirm password: ")

    if password != password_confirmation:
        raise ValueError("The passwords do not match.")

    return password


def print_validation_errors(error: ValidationError) -> None:
    """Print validation messages without exposing password input."""

    print("Administrator data validation failed:")

    for issue in error.errors(include_input=False):
        location = ".".join(str(item) for item in issue["loc"])
        print(f"- {location}: {issue['msg']}")


def main() -> int:
    """Create or promote an administrator account."""

    parser = build_argument_parser()
    arguments = parser.parse_args()
    normalized_email = arguments.email.strip().lower()

    with Session(engine) as database_session:
        user = user_repository.get_user_by_email(
            database_session,
            normalized_email,
        )

        if user is None:
            if not arguments.full_name:
                parser.error(
                    "--full-name is required when creating a new user."
                )

            try:
                password = read_new_user_password()
                user_data = UserCreate(
                    email=normalized_email,
                    full_name=arguments.full_name,
                    password=password,
                )
            except ValueError as error:
                print(f"Administrator creation failed: {error}")
                return 1
            except ValidationError as error:
                print_validation_errors(error)
                return 1

            try:
                user = auth_service.register_user(
                    database_session,
                    user_data,
                )
            except auth_service.EmailAlreadyRegisteredError as error:
                print(f"Administrator creation failed: {error}")
                return 1

        if user.role != UserRole.ADMIN:
            user = auth_service.change_user_role(
                database_session,
                user.id,
                UserRole.ADMIN,
            )

        if not user.is_active:
            user = auth_service.change_user_status(
                database_session,
                user.id,
                is_active=True,
            )

        print(
            "Administrator ready: "
            f"{user.email} ({user.role.value}, active)"
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAdministrator bootstrap cancelled.")
        raise SystemExit(130) from None
