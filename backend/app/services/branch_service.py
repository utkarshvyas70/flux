from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import List
from app.models.branch import Branch
from app.models.prompt_version import PromptVersion
from app.schemas.branch import BranchCreate
from app.services.repository_service import get_repository_by_id


def create_branch(
    db: Session,
    repository_id: UUID,
    data: BranchCreate,
    user_id: UUID,
) -> Branch:
    get_repository_by_id(db, repository_id, user_id)

    existing = (
        db.query(Branch)
        .filter(
            Branch.repository_id == repository_id,
            Branch.name == data.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Branch name already exists")

    if data.created_from_version_id:
        version = db.query(PromptVersion).filter(
            PromptVersion.id == data.created_from_version_id
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

    branch = Branch(
        repository_id=repository_id,
        name=data.name,
        created_from_version_id=data.created_from_version_id,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def get_branches(
    db: Session,
    repository_id: UUID,
    user_id: UUID,
) -> List[Branch]:
    get_repository_by_id(db, repository_id, user_id)
    return (
        db.query(Branch)
        .filter(Branch.repository_id == repository_id)
        .order_by(Branch.created_at.asc())
        .all()
    )


def get_or_create_main_branch(
    db: Session,
    repository_id: UUID,
    user_id: UUID,
) -> Branch:
    branch = (
        db.query(Branch)
        .filter(
            Branch.repository_id == repository_id,
            Branch.name == "main",
        )
        .first()
    )
    if not branch:
        branch = Branch(
            repository_id=repository_id,
            name="main",
            created_from_version_id=None,
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
    return branch