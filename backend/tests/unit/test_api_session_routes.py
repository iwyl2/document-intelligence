from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from document_intelligence.api.app import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "documents"
SIMPLE_PDF = FIXTURES_DIR / "simple_text.pdf"


@pytest.fixture(scope="module")
def api_client():
    """Provides a TestClient managing the FastAPI lifespan context."""
    with TestClient(app) as client:
        yield client


def test_api_session_isolation_upload_and_status(api_client):
    """
    Verifies that uploading a PDF into one session does not leak into
    another session when querying status.
    """
    session_alpha = "tenant_alpha_123"
    session_beta = "tenant_beta_456"

    # 1. Upload to Alpha
    with open(SIMPLE_PDF, "rb") as f:
        res = api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={"X-Session-ID": session_alpha},
        )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["file_name"] == "simple_text.pdf"
    assert data["num_chunks"] > 0

    # 2. Check Alpha status: must have chunks
    status_alpha = api_client.get(
        "/api/v1/documents/status",
        headers={"X-Session-ID": session_alpha},
    )
    assert status_alpha.status_code == 200
    alpha_data = status_alpha.json()
    assert alpha_data["total_chunks"] > 0
    assert "simple_text.pdf" in alpha_data["indexed_files"]
    assert alpha_data["is_empty"] is False

    # 3. Check Beta status: must remain empty
    status_beta = api_client.get(
        "/api/v1/documents/status",
        headers={"X-Session-ID": session_beta},
    )
    assert status_beta.status_code == 200
    beta_data = status_beta.json()
    assert beta_data["total_chunks"] == 0
    assert beta_data["indexed_files"] == []
    assert beta_data["is_empty"] is True


def test_api_selective_delete_leaves_other_session_intact(api_client):
    """
    Verifies that DELETE /documents on session Alpha clears Alpha
    while leaving Beta's documents completely intact.
    """
    session_alpha = "purge_session_a"
    session_beta = "keep_session_b"

    # Upload to Alpha
    with open(SIMPLE_PDF, "rb") as f:
        api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={"X-Session-ID": session_alpha},
        )

    # Upload to Beta
    with open(SIMPLE_PDF, "rb") as f:
        api_client.post(
            "/api/v1/documents/upload",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
            headers={"X-Session-ID": session_beta},
        )

    # Verify both have data
    assert api_client.get("/api/v1/documents/status", headers={"X-Session-ID": session_alpha}).json()["total_chunks"] > 0
    assert api_client.get("/api/v1/documents/status", headers={"X-Session-ID": session_beta}).json()["total_chunks"] > 0

    # Purge Alpha only
    del_res = api_client.delete("/api/v1/documents", headers={"X-Session-ID": session_alpha})
    assert del_res.status_code == 200

    # Assert Alpha is now empty
    status_a = api_client.get("/api/v1/documents/status", headers={"X-Session-ID": session_alpha}).json()
    assert status_a["total_chunks"] == 0
    assert status_a["is_empty"] is True

    # Assert Beta is still intact
    status_b = api_client.get("/api/v1/documents/status", headers={"X-Session-ID": session_beta}).json()
    assert status_b["total_chunks"] > 0
    assert status_b["is_empty"] is False


def test_api_session_query_parameter_fallback(api_client):
    """
    Verifies that the session_id query parameter fallback works
    for callers not using the X-Session-ID HTTP header.
    """
    session_query = "query_param_session_99"

    # Upload using query parameter
    with open(SIMPLE_PDF, "rb") as f:
        res = api_client.post(
            f"/api/v1/documents/upload?session_id={session_query}",
            files={"file": ("simple_text.pdf", f, "application/pdf")},
        )
    assert res.status_code == 201

    # Check status using query parameter
    status_res = api_client.get(f"/api/v1/documents/status?session_id={session_query}")
    assert status_res.status_code == 200
    assert status_res.json()["total_chunks"] > 0
