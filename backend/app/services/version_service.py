from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import List
from app.models.prompt_version import PromptVersion
from app.models.branch import Branch
from app.models.user import User
from app.schemas.prompt_version import PromptVersionCreate, PromptVersionResponse
from app.services.repository_service import get_repository_by_id


def commit_version(
    db: Session,
    repository_id: UUID,
    data: PromptVersionCreate,
    user_id: UUID,
) -> PromptVersion:
    get_repository_by_id(db, repository_id, user_id)

    branch = db.query(Branch).filter(Branch.id == data.branch_id).first()
    if not branch or str(branch.repository_id) != str(repository_id):
        raise HTTPException(status_code=404, detail="Branch not found")

    config_dict = data.get_config_dict()

    version = PromptVersion(
        branch_id=data.branch_id,
        prompt_text=data.prompt_text,
        model_config=config_dict,
        commit_message=data.commit_message,
        author_id=user_id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def get_versions(
    db: Session,
    repository_id: UUID,
    branch_id: UUID,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> List[PromptVersion]:
    get_repository_by_id(db, repository_id, user_id)

    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch or str(branch.repository_id) != str(repository_id):
        raise HTTPException(status_code=404, detail="Branch not found")

    return (
        db.query(PromptVersion)
        .filter(PromptVersion.branch_id == branch_id)
        .order_by(PromptVersion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_version_by_id(
    db: Session,
    version_id: UUID,
    user_id: UUID,
) -> PromptVersion:
    version = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    branch = db.query(Branch).filter(Branch.id == version.branch_id).first()
    get_repository_by_id(db, branch.repository_id, user_id)
    return version


def restore_version(
    db: Session,
    version_id: UUID,
    user_id: UUID,
) -> PromptVersion:
    original = get_version_by_id(db, version_id, user_id)

    all_versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.branch_id == original.branch_id)
        .all()
    )

    restored = PromptVersion(
        branch_id=original.branch_id,
        prompt_text=original.prompt_text,
        model_config=original.model_config,
        commit_message=f"Restored from v{len(all_versions)}",
        author_id=user_id,
    )
    db.add(restored)
    db.commit()
    db.refresh(restored)
    return restored


def enrich_version(
    db: Session,
    version: PromptVersion,
    index: int,
    total: int,
) -> PromptVersionResponse:
    user = db.query(User).filter(User.id == version.author_id).first()
    resp = PromptVersionResponse.model_validate(version)
    resp.author_name = user.name if user else "Unknown"
    resp.version_number = total - index
    return resp