import tempfile
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Header,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from document_intelligence.api.schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
)
from document_intelligence.auth.security import get_current_active_user
from document_intelligence.db.models import DocumentRecord, User, WorkspaceSession
from document_intelligence.db.session import get_db
from document_intelligence.services.rag_service import RagService

router = APIRouter(prefix="/api/v1", tags=["Document Intelligence"])


def get_rag_service(request: Request) -> RagService:
    """Dependency provider for RagService stored on app.state."""
    return request.app.state.rag_service


def get_session_id(
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    session_id: str | None = Query(default=None),
) -> str | None:
    """Extract session_id from X-Session-ID header, with query param fallback."""
    return x_session_id or session_id


def _resolve_workspace_session(
    session_id: str | None, current_user: User, db: Session
) -> WorkspaceSession:
    """
    Resolve and validate a WorkspaceSession for the current user.
    If session_id is None, falls back to the user's earliest workspace.
    Raises 404 if no valid workspace is found or if it belongs to another user.
    """
    if not session_id:
        workspace = (
            db.query(WorkspaceSession)
            .filter(WorkspaceSession.user_id == current_user.id)
            .order_by(WorkspaceSession.created_at.asc())
            .first()
        )
    else:
        workspace = (
            db.query(WorkspaceSession)
            .filter(
                WorkspaceSession.id == session_id,
                WorkspaceSession.user_id == current_user.id,
            )
            .first()
        )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )
    return workspace


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a PDF document",
)
async def upload_document(
    file: UploadFile = File(...),
    service: RagService = Depends(get_rag_service),
    session_id: str | None = Depends(get_session_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Accepts a PDF file, writes it to a temporary file,
    runs the ingestion/indexing pipeline, stores metadata in the relational DB,
    and cleans up the temp file.
    """
    workspace = _resolve_workspace_session(
        session_id=session_id, current_user=current_user, db=db
    )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported (.pdf).",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        result = service.index_document(
            file_path=temp_path, session_id=workspace.id, file_name=file.filename
        )

        document = DocumentRecord(
            session_id=workspace.id,
            file_name=file.filename,
            num_pages=result.num_pages,
            num_chunks=result.num_chunks,
        )
        db.add(document)
        db.commit()

        return UploadResponse(
            file_name=file.filename,
            num_pages=result.num_pages,
            num_chunks=result.num_chunks,
            message="Document successfully indexed.",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query indexed documents for grounded answers with citations",
)
def query_document(
    request: QueryRequest,
    service: RagService = Depends(get_rag_service),
    session_id: str | None = Depends(get_session_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    """
    Performs dense vector retrieval for the question and generates
    a grounded answer with inline [Page X] citations.
    """
    workspace = _resolve_workspace_session(
        session_id=session_id, current_user=current_user, db=db
    )

    response = service.query(
        question=request.question, top_k=request.top_k, session_id=workspace.id
    )
    return QueryResponse(
        answer=response.answer,
        cited_pages=response.cited_pages,
        is_grounded=response.is_grounded,
    )


@router.get("/documents/status", summary="Check in-memory vector store status")
def get_documents_status(
    service: RagService = Depends(get_rag_service),
    session_id: str | None = Depends(get_session_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    workspace = _resolve_workspace_session(
        session_id=session_id, current_user=current_user, db=db
    )
    return service.get_status(session_id=workspace.id)


@router.delete("/documents", summary="Clear all in-memory indexed documents")
def clear_documents(
    service: RagService = Depends(get_rag_service),
    session_id: str | None = Depends(get_session_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    workspace = _resolve_workspace_session(
        session_id=session_id, current_user=current_user, db=db
    )
    return service.clear_index(session_id=workspace.id)
