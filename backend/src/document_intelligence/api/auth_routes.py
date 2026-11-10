from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from document_intelligence.api.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserStatusUpdateRequest,
)
from document_intelligence.auth.security import (
    get_current_active_user,
    get_current_admin_user,
    security,
)
from document_intelligence.db.models import User, WorkspaceSession
from document_intelligence.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Access Control"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegisterRequest, db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.
    The first user in the system is automatically activated as an administrator.
    Subsequent users are created with `is_active=False` pending admin activation.
    """
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    is_first_user = db.query(User).count() == 0
    is_active = True if is_first_user else False
    is_admin = True if is_first_user else False

    hashed_pw = security.password_hash(data.password)
    user = User(
        email=data.email,
        password_hash=hashed_pw,
        is_active=is_active,
        is_admin=is_admin,
    )
    db.add(user)
    db.flush()

    default_session = WorkspaceSession(
        user_id=user.id,
        name="Default Workspace",
    )
    db.add(default_session)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive an access token",
)
async def login(
    data: UserLoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user with email and password.
    Rejects credentials if incorrect or if the account is not active.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending activation by an administrator.",
        )

    access_token = security.create_access_token(subject=user.id)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the profile information for the authenticated active user."""
    return current_user


@router.get(
    "/users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
)
async def list_users(
    _admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """Admin-only endpoint to inspect all registered user accounts and their statuses."""
    return db.query(User).order_by(User.created_at.asc()).all()


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate or deactivate a user account (Admin only)",
)
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Admin-only endpoint to activate or deactivate user accounts.
    Admins are prevented from deactivating their own account.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    if target_user.id == admin.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account.",
        )

    target_user.is_active = status_data.is_active
    db.commit()
    db.refresh(target_user)

    return target_user
