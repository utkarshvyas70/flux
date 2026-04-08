from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from app.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, InviteMemberRequest
from typing import List


def create_workspace(db: Session, data: WorkspaceCreate, user_id: UUID) -> Workspace:
    workspace = Workspace(name=data.name, owner_id=user_id)
    db.add(workspace)
    db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role=MemberRole.owner,
    )
    db.add(member)
    db.commit()
    db.refresh(workspace)
    return workspace


def get_my_workspaces(db: Session, user_id: UUID) -> List[Workspace]:
    memberships = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    )
    workspace_ids = [m.workspace_id for m in memberships]
    workspaces = (
        db.query(Workspace)
        .filter(Workspace.id.in_(workspace_ids))
        .order_by(Workspace.created_at.desc())
        .all()
    )
    return workspaces


def get_workspace_by_id(db: Session, workspace_id: UUID, user_id: UUID) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    return workspace


def invite_member(
    db: Session,
    workspace_id: UUID,
    data: InviteMemberRequest,
    current_user_id: UUID,
) -> WorkspaceMember:
    workspace = get_workspace_by_id(db, workspace_id, current_user_id)

    if str(workspace.owner_id) != str(current_user_id):
        raise HTTPException(status_code=403, detail="Only the owner can invite members")

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with that email not found")

    existing = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=data.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member_count(db: Session, workspace_id: UUID) -> int:
    return (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .count()
    )