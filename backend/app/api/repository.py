from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services import repository_service

router = APIRouter(prefix="/workspaces/{workspace_id}/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryResponse)
def create_repository(
    workspace_id: UUID,
    data: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = repository_service.create_repository(db, workspace_id, data, current_user.id)
    result = RepositoryResponse.model_validate(repo)
    result.branch_count = repository_service.get_branch_count(db, repo.id)
    result.last_updated = repository_service.get_last_updated(db, repo.id)
    return result


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repos = repository_service.get_repositories(db, workspace_id, current_user.id)
    result = []
    for r in repos:
        resp = RepositoryResponse.model_validate(r)
        resp.branch_count = repository_service.get_branch_count(db, r.id)
        resp.last_updated = repository_service.get_last_updated(db, r.id)
        result.append(resp)
    return result


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    workspace_id: UUID,
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = repository_service.get_repository_by_id(db, repository_id, current_user.id)
    result = RepositoryResponse.model_validate(repo)
    result.branch_count = repository_service.get_branch_count(db, repo.id)
    result.last_updated = repository_service.get_last_updated(db, repo.id)
    return result


@router.delete("/{repository_id}", status_code=204)
def delete_repository(
    workspace_id: UUID,
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository_service.delete_repository(db, repository_id, current_user.id)