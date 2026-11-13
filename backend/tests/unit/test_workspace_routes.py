from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from document_intelligence.api.app import app
from document_intelligence.api.routes import get_rag_service
from document_intelligence.db.models import Base, DocumentRecord, User, WorkspaceSession
from document_intelligence.db.session import get_db
from document_intelligence.services.rag_service import RagService


@pytest.fixture
def workspace_client():
    """Provides a TestClient with isolated in-memory SQLite and mocked RagService."""
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

    mock_rag_service = MagicMock(spec=RagService)
    mock_rag_service.clear_index.return_value = {"status": "cleared"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    with TestClient(app) as client:
        client.mock_rag = mock_rag_service
        client.testing_session = TestingSession
        yield client

    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, email: str, password: str = "securePassword123!") -> tuple[str, dict]:
    """Helper to register and login a user, returning (user_id, auth_headers)."""
    # Register (first user becomes active admin, others will need activation)
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201, reg_res.text
    user_id = reg_res.json()["id"]

    # If account is inactive, activate it using an admin session
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if login_res.status_code == 403:
        # Activate via direct DB or admin
        with client.testing_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            user.is_active = True
            session.commit()
        login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})

    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


def test_unauthenticated_request_blocked(workspace_client):
    """Accessing workspace endpoints without JWT Bearer token must return 401."""
    res = workspace_client.get("/api/v1/workspaces/")
    assert res.status_code == 401


def test_create_workspace_success(workspace_client):
    """Authenticated user can create a workspace and receive 201 Created."""
    _, headers = _register_and_login(workspace_client, "owner@corp.internal")

    res = workspace_client.post(
        "/api/v1/workspaces/",
        json={"name": "Financial Audits 2026"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["name"] == "Financial Audits 2026"
    assert "id" in data
    assert data["documents"] == []


def test_create_workspace_empty_name_fails(workspace_client):
    """Attempting to create a workspace with empty/whitespace name must return 400."""
    _, headers = _register_and_login(workspace_client, "owner@corp.internal")

    res = workspace_client.post(
        "/api/v1/workspaces/",
        json={"name": "   "},
        headers=headers,
    )
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"].lower()


def test_get_user_workspaces_lists_only_own_workspaces(workspace_client):
    """Users must only see their own workspaces, never other tenants'."""
    # 1. User Alpha creates a workspace
    _, headers_alpha = _register_and_login(workspace_client, "alpha@corp.internal")
    res_a = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Alpha Research"}, headers=headers_alpha
    )
    assert res_a.status_code == 201

    # 2. User Beta creates a workspace
    _, headers_beta = _register_and_login(workspace_client, "beta@corp.internal")
    res_b = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Beta Contracts"}, headers=headers_beta
    )
    assert res_b.status_code == 201

    # 3. Alpha lists workspaces: should include default + "Alpha Research", but NOT "Beta Contracts"
    list_alpha = workspace_client.get("/api/v1/workspaces/", headers=headers_alpha)
    assert list_alpha.status_code == 200
    alpha_names = [w["name"] for w in list_alpha.json()]
    assert "Alpha Research" in alpha_names
    assert "Beta Contracts" not in alpha_names

    # 4. Beta lists workspaces: should include default + "Beta Contracts", but NOT "Alpha Research"
    list_beta = workspace_client.get("/api/v1/workspaces/", headers=headers_beta)
    assert list_beta.status_code == 200
    beta_names = [w["name"] for w in list_beta.json()]
    assert "Beta Contracts" in beta_names
    assert "Alpha Research" not in beta_names


def test_get_workspace_by_id_success(workspace_client):
    """User can fetch their workspace by ID."""
    _, headers = _register_and_login(workspace_client, "reader@corp.internal")

    create_res = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Deep Learning"}, headers=headers
    )
    ws_id = create_res.json()["id"]

    get_res = workspace_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ws_id
    assert get_res.json()["name"] == "Deep Learning"


def test_get_workspace_cross_tenant_isolation_returns_404(workspace_client):
    """User Beta attempting to access User Alpha's workspace must receive 404 Not Found."""
    _, headers_alpha = _register_and_login(workspace_client, "alpha@corp.internal")
    create_res = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Confidential Alpha"}, headers=headers_alpha
    )
    alpha_ws_id = create_res.json()["id"]

    _, headers_beta = _register_and_login(workspace_client, "beta@corp.internal")

    # Beta attempts to read Alpha's workspace
    breach_res = workspace_client.get(f"/api/v1/workspaces/{alpha_ws_id}", headers=headers_beta)
    assert breach_res.status_code == 404
    assert "No workspace" in breach_res.json()["detail"]


def test_delete_workspace_success_and_clears_rag_index(workspace_client):
    """Deleting a workspace purges DB record and triggers vector store clearing."""
    _, headers = _register_and_login(workspace_client, "deleter@corp.internal")

    create_res = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Temporary Workspace"}, headers=headers
    )
    ws_id = create_res.json()["id"]

    # Delete workspace
    del_res = workspace_client.delete(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify vector store purge was called with correct session_id
    workspace_client.mock_rag.clear_index.assert_called_once_with(session_id=ws_id)

    # Verify workspace is gone from DB
    get_res = workspace_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert get_res.status_code == 404


def test_delete_workspace_cross_tenant_isolation_returns_404(workspace_client):
    """User Beta attempting to delete User Alpha's workspace must receive 404 and fail."""
    _, headers_alpha = _register_and_login(workspace_client, "alpha@corp.internal")
    create_res = workspace_client.post(
        "/api/v1/workspaces/", json={"name": "Protected Alpha"}, headers=headers_alpha
    )
    alpha_ws_id = create_res.json()["id"]

    _, headers_beta = _register_and_login(workspace_client, "beta@corp.internal")

    # Beta attempts to delete Alpha's workspace
    del_res = workspace_client.delete(f"/api/v1/workspaces/{alpha_ws_id}", headers=headers_beta)
    assert del_res.status_code == 404

    # Alpha's workspace must still exist
    check_res = workspace_client.get(f"/api/v1/workspaces/{alpha_ws_id}", headers=headers_alpha)
    assert check_res.status_code == 200


def test_workspace_with_documents_serialization(workspace_client):
    """Workspace with populated documents must serialize cleanly without validation errors."""
    user_id, headers = _register_and_login(workspace_client, "docowner@corp.internal")

    # Create workspace and seed document record in DB
    with workspace_client.testing_session() as session:
        ws = WorkspaceSession(user_id=user_id, name="Archive Workspace")
        session.add(ws)
        session.flush()

        doc = DocumentRecord(
            session_id=ws.id,
            file_name="annual_report.pdf",
            num_pages=15,
            num_chunks=42,
            uploaded_at=datetime.now(timezone.utc),
        )
        session.add(doc)
        session.commit()
        ws_id = ws.id

    # Fetch via API
    res = workspace_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data["documents"]) == 1
    doc_data = data["documents"][0]
    assert doc_data["file_name"] == "annual_report.pdf"
    assert doc_data["num_pages"] == 15
    assert doc_data["num_chunks"] == 42
