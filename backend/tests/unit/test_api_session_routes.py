from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from document_intelligence.api.app import app
from document_intelligence.db.models import Base, DocumentRecord, User, WorkspaceSession
from document_intelligence.db.session import get_db

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "documents"
SIMPLE_PDF = FIXTURES_DIR / "simple_text.pdf"


@pytest.fixture
def auth_api_client():
    """Provides a TestClient managing the lifespan context with an isolated in-memory DB."""
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
        client.testing_session = TestingSession
        yield client

    app.dependency_overrides.clear()


def _setup_user_and_workspace(
    client: TestClient, email: str, workspace_name: str = "Test Workspace"
) -> tuple[dict, str]:
    """Helper to register/activate user, create a workspace, and return (auth_headers, workspace_id)."""
    # 1. Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secureMasterPassword123!"},
    )
    assert reg_res.status_code == 201, reg_res.text
    user_id = reg_res.json()["id"]

    # 2. Login (activate if inactive)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secureMasterPassword123!"},
    )
    if login_res.status_code == 403:
        with client.testing_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            user.is_active = True
            session.commit()
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "secureMasterPassword123!"},
        )

    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create workspace
    ws_res = client.post(
        "/api/v1/workspaces/",
        json={"name": workspace_name},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    workspace_id = ws_res.json()["id"]

    return headers, workspace_id


def test_api_session_isolation_upload_and_status(auth_api_client):
    """
    Verifies that uploading a PDF into one session does not leak into
    another session when querying status, and verifies relational DocumentRecord persistence.
    """
    headers, session_alpha = _setup_user_and_workspace(
        auth_api_client, "tenant_a@corp.internal", "Alpha Workspace"
    )

    # Create a second workspace for the same user
    ws_beta_res = auth_api_client.post(
        "/api/v1/workspaces/",
        json={"name": "Beta Workspace"},
        headers=headers,
    )
    assert ws_beta_res.status_code == 201
    session_beta = ws_beta_res.json()["id"]

    # 1. Upload to Alpha
    headers_alpha = {**headers, "X-Session-ID": session_alpha}
    with open(SIMPLE_PDF, "rb") as f:
        res = auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers=headers_alpha,
        )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["file_name"] == "simple_text.pdf"
    assert data["num_chunks"] > 0

    # 2. Check Alpha status: must have chunks in vector store
    status_alpha = auth_api_client.get(
        "/api/v1/documents/status",
        headers=headers_alpha,
    )
    assert status_alpha.status_code == 200
    alpha_data = status_alpha.json()
    assert alpha_data["total_chunks"] > 0
    assert "simple_text.pdf" in alpha_data["indexed_files"]
    assert alpha_data["is_empty"] is False

    # 3. Check Beta status: must remain empty
    headers_beta = {**headers, "X-Session-ID": session_beta}
    status_beta = auth_api_client.get(
        "/api/v1/documents/status",
        headers=headers_beta,
    )
    assert status_beta.status_code == 200
    beta_data = status_beta.json()
    assert beta_data["total_chunks"] == 0
    assert beta_data["indexed_files"] == []
    assert beta_data["is_empty"] is True

    # 4. Verify Relational Control Plane Persistence: GET /workspaces/{id} has document
    ws_fetch = auth_api_client.get(
        f"/api/v1/workspaces/{session_alpha}",
        headers=headers,
    )
    assert ws_fetch.status_code == 200
    ws_data = ws_fetch.json()
    assert len(ws_data["documents"]) == 1
    assert ws_data["documents"][0]["file_name"] == "simple_text.pdf"
    assert ws_data["documents"][0]["num_chunks"] == data["num_chunks"]


def test_api_selective_delete_leaves_other_session_intact(auth_api_client):
    """
    Verifies that DELETE /documents on session Alpha clears Alpha
    while leaving Beta's documents completely intact.
    """
    headers, session_alpha = _setup_user_and_workspace(
        auth_api_client, "purge_user@corp.internal", "Purge Alpha"
    )

    ws_beta_res = auth_api_client.post(
        "/api/v1/workspaces/",
        json={"name": "Keep Beta"},
        headers=headers,
    )
    session_beta = ws_beta_res.json()["id"]

    headers_alpha = {**headers, "X-Session-ID": session_alpha}
    headers_beta = {**headers, "X-Session-ID": session_beta}

    # Upload to Alpha
    with open(SIMPLE_PDF, "rb") as f:
        auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers=headers_alpha,
        )

    # Upload to Beta
    with open(SIMPLE_PDF, "rb") as f:
        auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers=headers_beta,
        )

    # Verify both have data
    assert (
        auth_api_client.get("/api/v1/documents/status", headers=headers_alpha).json()[
            "total_chunks"
        ]
        > 0
    )
    assert (
        auth_api_client.get("/api/v1/documents/status", headers=headers_beta).json()[
            "total_chunks"
        ]
        > 0
    )

    # Purge Alpha only
    del_res = auth_api_client.delete(
        "/api/v1/documents", headers=headers_alpha
    )
    assert del_res.status_code == 200

    # Assert Alpha is now empty in vector store
    status_a = auth_api_client.get(
        "/api/v1/documents/status", headers=headers_alpha
    ).json()
    assert status_a["total_chunks"] == 0
    assert status_a["is_empty"] is True

    # Assert Alpha document records are purged from relational DB
    with auth_api_client.testing_session() as db:
        alpha_docs = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.session_id == session_alpha)
            .count()
        )
        assert alpha_docs == 0

        # Assert Beta document records remain intact in relational DB
        beta_docs = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.session_id == session_beta)
            .count()
        )
        assert beta_docs > 0

    # Assert Beta is still intact
    status_b = auth_api_client.get(
        "/api/v1/documents/status", headers=headers_beta
    ).json()
    assert status_b["total_chunks"] > 0
    assert status_b["is_empty"] is False


def test_api_session_query_parameter_fallback(auth_api_client):
    """
    Verifies that the session_id query parameter fallback works
    for callers not using the X-Session-ID HTTP header.
    """
    headers, session_id = _setup_user_and_workspace(
        auth_api_client, "query_user@corp.internal", "Query Param WS"
    )

    # Upload using query parameter
    with open(SIMPLE_PDF, "rb") as f:
        res = auth_api_client.post(
            f"/api/v1/documents/upload?session_id={session_id}",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers=headers,
        )
    assert res.status_code == 201

    # Check status using query parameter
    status_res = auth_api_client.get(
        f"/api/v1/documents/status?session_id={session_id}",
        headers=headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["total_chunks"] > 0


def test_upload_cross_tenant_rejected_with_404(auth_api_client):
    """
    User Beta attempting to upload a document to User Alpha's workspace must receive 404 Not Found.
    """
    # 1. User Alpha creates workspace
    _, ws_alpha_id = _setup_user_and_workspace(
        auth_api_client, "user_alpha@corp.internal", "Alpha Secret WS"
    )

    # 2. User Beta registers
    headers_beta, _ = _setup_user_and_workspace(
        auth_api_client, "user_beta@corp.internal", "Beta Normal WS"
    )

    # 3. User Beta attempts to upload to User Alpha's workspace
    with open(SIMPLE_PDF, "rb") as f:
        res = auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={**headers_beta, "X-Session-ID": ws_alpha_id},
        )
    assert res.status_code == 404
    assert "Workspace not found" in res.json()["detail"]


def test_upload_without_session_id_falls_back_to_default_workspace(auth_api_client):
    """
    Uploading without X-Session-ID header automatically routes to the user's default workspace.
    """
    headers, _ = _setup_user_and_workspace(
        auth_api_client, "default_user@corp.internal", "Custom WS"
    )

    # Upload with NO X-Session-ID header
    with open(SIMPLE_PDF, "rb") as f:
        res = auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers=headers,
        )
    assert res.status_code == 201
    assert res.json()["num_chunks"] > 0

    # Query status with NO X-Session-ID header (should resolve to the same default workspace)
    status_res = auth_api_client.get(
        "/api/v1/documents/status",
        headers=headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["total_chunks"] > 0


def test_delete_single_document_dual_plane_purge(auth_api_client):
    """
    Verifies that DELETE /api/v1/documents/{document_id} deletes chunks from vector storage
    and deletes the DocumentRecord row from the relational database.
    """
    headers, ws_id = _setup_user_and_workspace(
        auth_api_client, "single_del@corp.internal", "Single Del WS"
    )

    # 1. Upload document
    with open(SIMPLE_PDF, "rb") as f:
        upload_res = auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={**headers, "X-Session-ID": ws_id},
        )
    assert upload_res.status_code == 201

    # Get document id from workspace
    ws_res = auth_api_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert ws_res.status_code == 200
    docs = ws_res.json()["documents"]
    assert len(docs) == 1
    doc_id = docs[0]["id"]

    # 2. Delete the single document
    del_res = auth_api_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={**headers, "X-Session-ID": ws_id},
    )
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # 3. Verify vector storage is empty
    status_res = auth_api_client.get(
        "/api/v1/documents/status",
        headers={**headers, "X-Session-ID": ws_id},
    )
    assert status_res.json()["total_chunks"] == 0

    # 4. Verify relational DB row is deleted
    with auth_api_client.testing_session() as db:
        remaining_docs = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.id == doc_id)
            .count()
        )
        assert remaining_docs == 0


def test_delete_single_document_cross_tenant_rejected_with_404(auth_api_client):
    """
    Verifies that User Beta cannot delete User Alpha's document (returns 404).
    """
    # 1. User Alpha creates document
    headers_alpha, ws_alpha_id = _setup_user_and_workspace(
        auth_api_client, "alpha_owner@corp.internal", "Alpha Owner WS"
    )
    with open(SIMPLE_PDF, "rb") as f:
        auth_api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={**headers_alpha, "X-Session-ID": ws_alpha_id},
        )
    ws_res = auth_api_client.get(f"/api/v1/workspaces/{ws_alpha_id}", headers=headers_alpha)
    doc_id = ws_res.json()["documents"][0]["id"]

    # 2. User Beta registers
    headers_beta, ws_beta_id = _setup_user_and_workspace(
        auth_api_client, "beta_attacker@corp.internal", "Beta WS"
    )

    # 3. User Beta tries to delete User Alpha's doc using User Beta's session
    del_res = auth_api_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={**headers_beta, "X-Session-ID": ws_beta_id},
    )
    assert del_res.status_code == 404
    assert "not found" in del_res.json()["detail"].lower()
