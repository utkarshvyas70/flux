from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import List
from app.models.eval import EvalSuite, EvalCase, EvalRun, EvalRunStatus
from app.models.prompt_version import PromptVersion
from app.schemas.eval import EvalSuiteCreate, EvalCaseCreate
from app.services.repository_service import get_repository_by_id


def create_suite(
    db: Session,
    repository_id: UUID,
    data: EvalSuiteCreate,
    user_id: UUID,
) -> EvalSuite:
    get_repository_by_id(db, repository_id, user_id)
    suite = EvalSuite(repository_id=repository_id, name=data.name)
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


def get_suites(
    db: Session,
    repository_id: UUID,
    user_id: UUID,
) -> List[EvalSuite]:
    get_repository_by_id(db, repository_id, user_id)
    return (
        db.query(EvalSuite)
        .filter(EvalSuite.repository_id == repository_id)
        .order_by(EvalSuite.created_at.desc())
        .all()
    )


def delete_suite(db: Session, suite_id: UUID, user_id: UUID) -> None:
    suite = db.query(EvalSuite).filter(EvalSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    get_repository_by_id(db, suite.repository_id, user_id)
    db.delete(suite)
    db.commit()


def add_case(
    db: Session,
    suite_id: UUID,
    data: EvalCaseCreate,
    user_id: UUID,
) -> EvalCase:
    suite = db.query(EvalSuite).filter(EvalSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    get_repository_by_id(db, suite.repository_id, user_id)
    case = EvalCase(
        suite_id=suite_id,
        input_text=data.input_text,
        expected_output=data.expected_output,
        eval_type=data.eval_type,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_cases(
    db: Session,
    suite_id: UUID,
    user_id: UUID,
) -> List[EvalCase]:
    suite = db.query(EvalSuite).filter(EvalSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    get_repository_by_id(db, suite.repository_id, user_id)
    return db.query(EvalCase).filter(EvalCase.suite_id == suite_id).all()


def delete_case(db: Session, case_id: UUID, user_id: UUID) -> None:
    case = db.query(EvalCase).filter(EvalCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    suite = db.query(EvalSuite).filter(EvalSuite.id == case.suite_id).first()
    get_repository_by_id(db, suite.repository_id, user_id)
    db.delete(case)
    db.commit()


def trigger_eval_run(
    db: Session,
    version_id: UUID,
    suite_id: UUID,
    user_id: UUID,
) -> EvalRun:
    version = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    suite = db.query(EvalSuite).filter(EvalSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")

    cases = db.query(EvalCase).filter(EvalCase.suite_id == suite_id).all()
    if not cases:
        raise HTTPException(status_code=400, detail="Suite has no test cases")

    run = EvalRun(
        version_id=version_id,
        suite_id=suite_id,
        status=EvalRunStatus.pending,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_eval_run(db: Session, run_id: UUID) -> EvalRun:
    run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return run