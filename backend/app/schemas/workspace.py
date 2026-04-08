from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.workspace import MemberRole


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceMemberResponse(BaseModel):
    user_id: UUID
    role: MemberRole

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime
    member_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str
    role: MemberRole = MemberRole.member