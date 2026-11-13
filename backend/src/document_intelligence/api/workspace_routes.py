from typing import List

from document_intelligence.api.routes import get_rag_service
from document_intelligence.api.schemas import (
    DocumentRecordResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
)
from document_intelligence.auth.security import get_current_active_user
from document_intelligence.db.models import DocumentRecord, User, WorkspaceSession
from document_intelligence.db.session import get_db
from document_intelligence.services.rag_service import RagService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/workspaces", tags=["User workspace management"])


@router.get(
    "/",
    response_model=List[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all the workspaces for the current user",
)
async def get_user_workspaces(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> List[WorkspaceResponse]:
    return (
        db.query(WorkspaceSession)
        .filter(WorkspaceSession.user_id == current_user.id)
        .order_by(WorkspaceSession.created_at.desc())
        .all()
    )


@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
)
async def create_workspace(
    data: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    cleaned_name = data.name.strip()

    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace name cannot be empty or contain only whitespace.",
        )

    workspace = WorkspaceSession(user_id=current_user.id, name=cleaned_name)

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Search workspace from ID",
)
async def find_workspace_by_id(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    return _retrieve_and_validate_workspace(
        workspace_id=workspace_id, db=db, current_user=current_user
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workspace",
)
async def remove_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    rag_service: RagService = Depends(get_rag_service),
) -> None:
    workspace = _retrieve_and_validate_workspace(
        workspace_id=workspace_id, db=db, current_user=current_user
    )

    rag_service.clear_index(session_id=workspace_id)
    db.delete(workspace)
    db.commit()


def _retrieve_and_validate_workspace(
    workspace_id: str, db: Session, current_user: User
) -> WorkspaceSession:
    if not workspace_id or not workspace_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace id.",
        )

    workspace = (
        db.query(WorkspaceSession)
        .filter(
            WorkspaceSession.id == workspace_id,
            WorkspaceSession.user_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workspace for the given ID",
        )

    return workspace
