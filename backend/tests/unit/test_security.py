from datetime import timedelta
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from document_intelligence.auth.security import Security, get_current_user
from document_intelligence.db.models import Base, User


@pytest.fixture
def auth_security():
    return Security()


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_password_hash_and_verification(auth_security):
    raw_password = "mySecretPassword123!"

    # 1. Hash password
    hashed = auth_security.password_hash(raw_password)
    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # 2. Salts must be unique (hashing twice yields different hashes)
    hashed_again = auth_security.password_hash(raw_password)
    assert hashed != hashed_again

    # 3. Verification must succeed for correct password
    assert auth_security.verify_password(raw_password, hashed) is True

    # 4. Verification must fail for incorrect password
    assert auth_security.verify_password("wrongPassword123!", hashed) is False


def test_create_and_decode_access_token(auth_security):
    subject = "user_alpha_123"

    token = auth_security.create_access_token(subject=subject)
    assert isinstance(token, str)

    payload = auth_security.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == subject
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_expired_access_token_returns_none(auth_security):
    subject = "user_expired_999"

    # Create token expired 10 minutes ago
    expired_token = auth_security.create_access_token(
        subject=subject, expires_delta=timedelta(minutes=-10)
    )

    payload = auth_security.decode_access_token(expired_token)
    assert payload is None


def test_tampered_access_token_returns_none(auth_security):
    token = auth_security.create_access_token(subject="user_real")
    tampered_token = token[:-5] + "abcde"

    payload = auth_security.decode_access_token(tampered_token)
    assert payload is None


def test_get_current_user_success(auth_security, memory_db):
    # 1. Seed user in DB
    user = User(
        email="student@university.edu",
        password_hash=auth_security.password_hash("pass123"),
    )
    memory_db.add(user)
    memory_db.commit()

    # 2. Generate token for user
    token = auth_security.create_access_token(subject=user.id)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # 3. Resolve user via dependency
    resolved_user = get_current_user(credentials=credentials, db=memory_db)
    assert resolved_user.id == user.id
    assert resolved_user.email == "student@university.edu"


def test_get_current_user_invalid_token(memory_db):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.jwt.token")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=memory_db)

    assert exc_info.value.status_code == 401
    assert "Invalid or expired authentication token" in exc_info.value.detail


def test_get_current_user_non_existent_in_db(auth_security, memory_db):
    token = auth_security.create_access_token(subject="non_existent_user_id")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=memory_db)

    assert exc_info.value.status_code == 401
    assert "User not found" in exc_info.value.detail
