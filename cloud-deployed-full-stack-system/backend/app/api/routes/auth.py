"""API routes for user registration and authentication."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentUser, DatabaseSession
from app.core.config import get_settings
from app.schemas.user import TokenResponse, UserCreate, UserResponse
import app.services.auth as auth_service


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

OAuth2LoginForm = Annotated[
    OAuth2PasswordRequestForm,
    Depends(),
]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
def register_user(
    user_data: UserCreate,
    database_session: DatabaseSession,
) -> UserResponse:
    """Register a new user with the default viewer role."""

    try:
        return auth_service.register_user(
            database_session,
            user_data,
        )
    except auth_service.EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Create an access token",
)
def login_for_access_token(
    form_data: OAuth2LoginForm,
    database_session: DatabaseSession,
) -> TokenResponse:
    """Authenticate OAuth2 form credentials and return a bearer token."""

    try:
        user = auth_service.authenticate_user(
            database_session,
            email=form_data.username,
            password=form_data.password,
        )
    except auth_service.InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except auth_service.InactiveUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    settings = get_settings()

    return TokenResponse(
        access_token=auth_service.create_user_access_token(user),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user",
)
def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Return the user represented by the current bearer token."""

    return current_user
