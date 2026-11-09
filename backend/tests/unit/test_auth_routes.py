import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from document_intelligence.api.app import app
from document_intelligence.db.models import Base, User
from document_intelligence.db.session import get_db


@pytest.fixture
def auth_client():
    """Provides a TestClient with an isolated in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_first_user_registration_is_active_admin(auth_client):
    """The first registered user must automatically be an active administrator."""
    res = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "superadmin@corp.internal", "password": "secureMasterPassword123!"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["email"] == "superadmin@corp.internal"
    assert data["is_active"] is True
    assert data["is_admin"] is True
    assert "id" in data


def test_subsequent_user_registration_is_inactive(auth_client):
    """Subsequent registrations must default to inactive (is_active=False, is_admin=False)."""
    # 1. Register first admin
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "admin@corp.internal", "password": "adminPassword123!"},
    )

    # 2. Register standard user
    res = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "analyst@corp.internal", "password": "analystPassword123!"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["email"] == "analyst@corp.internal"
    assert data["is_active"] is False
    assert data["is_admin"] is False


def test_duplicate_email_registration_fails(auth_client):
    """Attempting to register with an existing email must return 400 Bad Request."""
    payload = {"email": "duplicate@corp.internal", "password": "password123!"}
    res1 = auth_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = auth_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_inactive_user_login_is_forbidden(auth_client):
    """Inactive users must be blocked from logging in with 403 Forbidden."""
    # First admin
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "root@corp.internal", "password": "rootPassword123!"},
    )

    # Inactive user
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "pending@corp.internal", "password": "pendingPassword123!"},
    )

    # Attempt login
    res = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "pending@corp.internal", "password": "pendingPassword123!"},
    )
    assert res.status_code == 403
    assert "pending activation" in res.json()["detail"]


def test_login_invalid_credentials(auth_client):
    """Invalid email or password must return 401 Unauthorized."""
    # Register active user
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "valid@corp.internal", "password": "correctPassword123!"},
    )

    # Wrong password
    res1 = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "valid@corp.internal", "password": "wrongPassword123!"},
    )
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["detail"]

    # Non-existent user
    res2 = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@corp.internal", "password": "correctPassword123!"},
    )
    assert res2.status_code == 401


def test_active_user_login_and_me_profile(auth_client):
    """Active user can log in, receive a JWT token, and inspect their profile via /auth/me."""
    # 1. Register first admin
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "active@corp.internal", "password": "activePassword123!"},
    )

    # 2. Login
    login_res = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "active@corp.internal", "password": "activePassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Access /auth/me
    token = token_data["access_token"]
    me_res = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["email"] == "active@corp.internal"
    assert profile["is_active"] is True
    assert profile["is_admin"] is True


def test_admin_user_activation_flow(auth_client):
    """Admin can list users, activate a pending account, allowing subsequent login."""
    # 1. Register admin
    admin_reg = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "sysadmin@corp.internal", "password": "adminPassword123!"},
    )
    admin_id = admin_reg.json()["id"]

    # 2. Register user (inactive)
    user_reg = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "newbie@corp.internal", "password": "newbiePassword123!"},
    )
    user_id = user_reg.json()["id"]

    # 3. Admin logs in
    admin_login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "sysadmin@corp.internal", "password": "adminPassword123!"},
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Admin lists users
    users_res = auth_client.get("/api/v1/auth/users", headers=admin_headers)
    assert users_res.status_code == 200
    users_list = users_res.json()
    assert len(users_list) == 2

    # 5. Admin activates user
    activate_res = auth_client.patch(
        f"/api/v1/auth/users/{user_id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert activate_res.status_code == 200
    assert activate_res.json()["is_active"] is True

    # 6. User can now log in successfully
    user_login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "newbie@corp.internal", "password": "newbiePassword123!"},
    )
    assert user_login.status_code == 200
    assert "access_token" in user_login.json()

    # 7. Admin cannot deactivate own account
    self_deactivate = auth_client.patch(
        f"/api/v1/auth/users/{admin_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert self_deactivate.status_code == 400
    assert "cannot deactivate" in self_deactivate.json()["detail"].lower()
