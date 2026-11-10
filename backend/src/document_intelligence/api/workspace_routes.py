from typing import List

from document_intelligence.api.schemas import DocumentRecordResponse, WorkspaceResponse
from document_intelligence.auth.security import get_current_active_user
from document_intelligence.db.models import DocumentRecord, User, WorkspaceSession
from document_intelligence.db.session import get_db
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/workspaces", tags=["User workspace management"])


@router.get(
    "/",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all the workspaces for the current user",
)
async def get_user_workspaces(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> List[WorkspaceResponse]:
    workspaces = db.query(WorkspaceSession).filter(
        WorkspaceSession.user_id == current_user.id
    )

    workspace_responses = []

    for workspace in workspaces:
        workspace_responses.append(_workspace_to_response(workspace=workspace))

    return workspace_responses


def _workspace_to_response(workspace: WorkspaceSession) -> WorkspaceResponse:
    documents = []
    for document in workspace.documents:
        documents.append(_document_to_response(document=document))

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        created_at=workspace.created_at,
        documents=documents,
    )


def _document_to_response(document: DocumentRecord) -> DocumentRecordResponse:
    return DocumentRecordResponse(
        id=document.id,
        file_name=document.file_name,
        num_pages=document.num_pages,
        num_chunks=document.num_chunks,
        uploaded_at=document.uploaded_at,
    )
