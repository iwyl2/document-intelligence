import os
from dotenv import load_dotenv
import bcrypt
from datetime import timedelta, datetime, timezone
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from fastapi import Depends, HTTPException, status
from document_intelligence.db.models import User
from document_intelligence.db.session import get_db
from sqlalchemy.orm import Session

load_dotenv()
http_bearer = HTTPBearer()


class Security:
    def __init__(self):
        self.secret_key = os.getenv(
            "JWT_SECRET", "dev-secret-key-for-local-testing-only"
        )
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_mins = int(os.getenv("JWT_EXPIRE_MINUTES", 30))

    def password_hash(self, plain_password: str) -> str:
        return bcrypt.hashpw(
            password=plain_password.encode("utf-8"), salt=bcrypt.gensalt()
        ).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password=password.encode("utf-8"), hashed_password=hashed.encode("utf-8")
        )

    def create_access_token(
        self, subject: str, expires_delta: timedelta | None = None
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + (expires_delta or timedelta(minutes=self.jwt_expire_mins)),
        }
        return jwt.encode(
            payload=payload, key=self.secret_key, algorithm=self.algorithm
        )

    def decode_access_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, key=self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError:
            return None


security = Security()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """FastAPI Dependency: extracts and verifies User from Bearer token."""
    token = credentials.credentials
    payload = security.decode_access_token(token=token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """FastAPI Dependency: verifies the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact an administrator.",
        )
    return current_user


def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """FastAPI Dependency: verifies the authenticated user has admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )
    return current_user
