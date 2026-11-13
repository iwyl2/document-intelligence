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
