from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import List
from datetime import datetime
from app.models.repository import Repository
from app.models.branch import Branch
from app.schemas.repository import RepositoryCreate
from app.services.workspace_service import get_workspace_by_id


def create_repository(
    db: Session,
    workspace_id: UUID,
    data: RepositoryCreate,
    user_id: UUID,
) -> Repository:
    get_workspace_by_id(db, workspace_id, user_id)

    repo = Repository(
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def get_repositories(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
) -> List[Repository]:
    get_workspace_by_id(db, workspace_id, user_id)

    repos = (
        db.query(Repository)
        .filter(Repository.workspace_id == workspace_id)
        .order_by(Repository.created_at.desc())
        .all()
    )
    return repos


def get_repository_by_id(
    db: Session,
    repository_id: UUID,
    user_id: UUID,
) -> Repository:
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    get_workspace_by_id(db, repo.workspace_id, user_id)
    return repo


def delete_repository(
    db: Session,
    repository_id: UUID,
    user_id: UUID,
) -> None:
    repo = get_repository_by_id(db, repository_id, user_id)
    db.delete(repo)
    db.commit()


def get_branch_count(db: Session, repository_id: UUID) -> int:
    return (
        db.query(Branch)
        .filter(Branch.repository_id == repository_id)
        .count()
    )


def get_last_updated(db: Session, repository_id: UUID):
    branch = (
        db.query(Branch)
        .filter(Branch.repository_id == repository_id)
        .order_by(Branch.created_at.desc())
        .first()
    )
    return branch.created_at if branch else None