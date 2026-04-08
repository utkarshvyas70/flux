from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class RepositoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    branch_count: Optional[int] = 0
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}