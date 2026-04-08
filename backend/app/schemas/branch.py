from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class BranchCreate(BaseModel):
    name: str
    created_from_version_id: Optional[UUID] = None


class BranchResponse(BaseModel):
    id: UUID
    repository_id: UUID
    name: str
    created_from_version_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}