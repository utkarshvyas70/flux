from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.branch import Branch
from app.models.prompt_version import PromptVersion
from app.schemas.branch import BranchCreate, BranchResponse
from app.schemas.prompt_version import PromptVersionCreate, PromptVersionResponse
from app.services import branch_service, version_service

router = APIRouter(prefix="/repositories/{repository_id}", tags=["versions"])


@router.post("/branches", response_model=BranchResponse)
def create_branch(
    repository_id: UUID,
    data: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return branch_service.create_branch(db, repository_id, data, current_user.id)


@router.get("/branches", response_model=List[BranchResponse])
def list_branches(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return branch_service.get_branches(db, repository_id, current_user.id)


@router.post("/versions", response_model=PromptVersionResponse)
def commit_version(
    repository_id: UUID,
    data: PromptVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = version_service.commit_version(db, repository_id, data, current_user.id)
    all_versions = version_service.get_versions(
        db, repository_id, data.branch_id, current_user.id
    )
    return version_service.enrich_version(db, version, 0, len(all_versions))


@router.get("/versions", response_model=List[PromptVersionResponse])
def list_versions(
    repository_id: UUID,
    branch_id: UUID = Query(...),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    versions = version_service.get_versions(
        db, repository_id, branch_id, current_user.id, skip, limit
    )
    total = len(versions)
    return [
        version_service.enrich_version(db, v, i, total)
        for i, v in enumerate(versions)
    ]


@router.post("/initialize", response_model=BranchResponse)
def initialize_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return branch_service.get_or_create_main_branch(db, repository_id, current_user.id)


router2 = APIRouter(prefix="/versions", tags=["versions"])


@router2.get("/{version_id}", response_model=PromptVersionResponse)
def get_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = version_service.get_version_by_id(db, version_id, current_user.id)
    all_versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.branch_id == version.branch_id)
        .all()
    )
    idx = next(
        (i for i, v in enumerate(all_versions) if str(v.id) == str(version_id)), 0
    )
    return version_service.enrich_version(db, version, idx, len(all_versions))


@router2.post("/{version_id}/restore", response_model=PromptVersionResponse)
def restore_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = version_service.restore_version(db, version_id, current_user.id)
    return version_service.enrich_version(db, version, 0, 1)