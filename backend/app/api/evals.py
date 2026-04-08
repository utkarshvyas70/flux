from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.eval import EvalCase
from app.schemas.eval import (
    EvalSuiteCreate,
    EvalSuiteResponse,
    EvalCaseCreate,
    EvalCaseResponse,
    EvalRunResponse,
    TriggerEvalRequest,
)
from app.services import eval_service
from app.workers.eval_worker import process_eval_run

router = APIRouter(tags=["evals"])


@router.post("/repositories/{repository_id}/suites", response_model=EvalSuiteResponse)
def create_suite(
    repository_id: UUID,
    data: EvalSuiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suite = eval_service.create_suite(db, repository_id, data, current_user.id)
    case_count = db.query(EvalCase).filter(EvalCase.suite_id == suite.id).count()
    result = EvalSuiteResponse.model_validate(suite)
    result.case_count = case_count
    return result


@router.get("/repositories/{repository_id}/suites", response_model=List[EvalSuiteResponse])
def list_suites(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suites = eval_service.get_suites(db, repository_id, current_user.id)
    result = []
    for s in suites:
        r = EvalSuiteResponse.model_validate(s)
        r.case_count = db.query(EvalCase).filter(EvalCase.suite_id == s.id).count()
        result.append(r)
    return result


@router.delete("/suites/{suite_id}", status_code=204)
def delete_suite(
    suite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eval_service.delete_suite(db, suite_id, current_user.id)


@router.post("/suites/{suite_id}/cases", response_model=EvalCaseResponse)
def add_case(
    suite_id: UUID,
    data: EvalCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return eval_service.add_case(db, suite_id, data, current_user.id)


@router.get("/suites/{suite_id}/cases", response_model=List[EvalCaseResponse])
def list_cases(
    suite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return eval_service.get_cases(db, suite_id, current_user.id)


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eval_service.delete_case(db, case_id, current_user.id)


@router.post("/versions/{version_id}/eval-runs", response_model=EvalRunResponse)
def trigger_eval_run(
    version_id: UUID,
    data: TriggerEvalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = eval_service.trigger_eval_run(db, version_id, data.suite_id, current_user.id)
    background_tasks.add_task(process_eval_run, str(run.id))
    return run


@router.get("/eval-runs/{run_id}", response_model=EvalRunResponse)
def get_eval_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return eval_service.get_eval_run(db, run_id)