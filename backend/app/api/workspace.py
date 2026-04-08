from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    InviteMemberRequest,
    WorkspaceMemberResponse,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.create_workspace(db, data, current_user.id)
    member_count = workspace_service.get_member_count(db, workspace.id)
    result = WorkspaceResponse.model_validate(workspace)
    result.member_count = member_count
    return result


@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = workspace_service.get_my_workspaces(db, current_user.id)
    result = []
    for w in workspaces:
        r = WorkspaceResponse.model_validate(w)
        r.member_count = workspace_service.get_member_count(db, w.id)
        result.append(r)
    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.get_workspace_by_id(db, workspace_id, current_user.id)
    result = WorkspaceResponse.model_validate(workspace)
    result.member_count = workspace_service.get_member_count(db, workspace.id)
    return result


@router.post("/{workspace_id}/invite")
def invite_member(
    workspace_id: UUID,
    data: InviteMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_service.invite_member(db, workspace_id, data, current_user.id)
    return {"message": "Member invited successfully"}