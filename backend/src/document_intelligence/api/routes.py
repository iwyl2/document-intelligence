import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from document_intelligence.api.schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
)
from document_intelligence.services.rag_service import RagService

router = APIRouter(prefix="/api/v1", tags=["Document Intelligence"])


def get_rag_service(request: Request) -> RagService:
    """Dependency provider for RagService stored on app.state."""
    return request.app.state.rag_service


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a PDF document",
)
async def upload_document(
    file: UploadFile = File(...), service: RagService = Depends(get_rag_service)
) -> UploadResponse:
    """
    Accepts a PDF file, writes it to a temporary file,
    runs the ingestion/indexing pipeline, and cleans up the temp file.
    """

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
        result = service.index_document(file_path=temp_path)
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
) -> QueryResponse:
    """
    Performs dense vector retrieval for the question and generates
    a grounded answer with inline [Page X] citations.
    """
    response = service.query(question=request.question, top_k=request.top_k)
    return QueryResponse(
        answer=response.answer,
        cited_pages=response.cited_pages,
        is_grounded=response.is_grounded,
    )
