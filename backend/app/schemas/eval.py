from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any
from app.models.eval import EvalType, EvalRunStatus


class EvalCaseCreate(BaseModel):
    input_text: str
    expected_output: str
    eval_type: EvalType = EvalType.exact


class EvalCaseResponse(BaseModel):
    id: UUID
    suite_id: UUID
    input_text: str
    expected_output: str
    eval_type: EvalType

    model_config = {"from_attributes": True}


class EvalSuiteCreate(BaseModel):
    name: str


class EvalSuiteResponse(BaseModel):
    id: UUID
    repository_id: UUID
    name: str
    created_at: datetime
    case_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class EvalRunResponse(BaseModel):
    id: UUID
    version_id: UUID
    suite_id: UUID
    status: EvalRunStatus
    overall_score: Optional[float]
    results: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class TriggerEvalRequest(BaseModel):
    suite_id: UUID