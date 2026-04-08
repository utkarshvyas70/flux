from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import difflib
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.prompt_version import PromptVersion
from app.models.eval import EvalRun, EvalCase, EvalRunStatus
from app.models.branch import Branch
from app.services.repository_service import get_repository_by_id

router = APIRouter(tags=["diff"])


def get_text_diff(text_a: str, text_b: str) -> list:
    matcher = difflib.SequenceMatcher(None, text_a, text_b)
    diff = []
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        diff.append({
            "op": opcode,
            "text_a": text_a[a0:a1],
            "text_b": text_b[b0:b1],
        })
    return diff


def get_config_diff(config_a: dict, config_b: dict) -> list:
    all_keys = set(list(config_a.keys()) + list(config_b.keys()))
    changes = []
    for key in all_keys:
        val_a = config_a.get(key)
        val_b = config_b.get(key)
        if val_a != val_b:
            changes.append({
                "field": key,
                "value_a": val_a,
                "value_b": val_b,
                "changed": True,
            })
        else:
            changes.append({
                "field": key,
                "value_a": val_a,
                "value_b": val_b,
                "changed": False,
            })
    return changes


def get_best_eval_run(db: Session, version_id: UUID) -> Optional[EvalRun]:
    return (
        db.query(EvalRun)
        .filter(
            EvalRun.version_id == version_id,
            EvalRun.status == EvalRunStatus.completed,
        )
        .order_by(EvalRun.created_at.desc())
        .first()
    )


def get_behavioral_diff(run_a: EvalRun, run_b: EvalRun) -> dict:
    if not run_a or not run_b:
        return {"available": False, "reason": "One or both versions have no completed eval runs"}

    if str(run_a.suite_id) != str(run_b.suite_id):
        return {"available": False, "reason": "Versions were evaluated on different suites"}

    results_a = {r["case_id"]: r for r in (run_a.results or [])}
    results_b = {r["case_id"]: r for r in (run_b.results or [])}
    common_cases = set(results_a.keys()) & set(results_b.keys())

    if not common_cases:
        return {"available": False, "reason": "No common test cases found"}

    cases = []
    for case_id in common_cases:
        ra = results_a[case_id]
        rb = results_b[case_id]
        score_delta = round(rb["score"] - ra["score"], 4)
        output_changed = ra["actual_output"].strip() != rb["actual_output"].strip()
        cases.append({
            "case_id": case_id,
            "input_text": ra["input_text"],
            "expected_output": ra["expected_output"],
            "output_a": ra["actual_output"],
            "output_b": rb["actual_output"],
            "score_a": ra["score"],
            "score_b": rb["score"],
            "score_delta": score_delta,
            "output_changed": output_changed,
            "eval_type": ra["eval_type"],
        })

    cases.sort(key=lambda x: abs(x["score_delta"]), reverse=True)

    return {
        "available": True,
        "suite_id": str(run_a.suite_id),
        "cases": cases,
        "score_a": run_a.overall_score,
        "score_b": run_b.overall_score,
        "score_delta": round(
            (run_b.overall_score or 0) - (run_a.overall_score or 0), 2
        ),
    }


@router.get("/diff")
def get_diff(
    version_a: UUID = Query(...),
    version_b: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ver_a = db.query(PromptVersion).filter(PromptVersion.id == version_a).first()
    ver_b = db.query(PromptVersion).filter(PromptVersion.id == version_b).first()

    if not ver_a or not ver_b:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="One or both versions not found")

    branch_a = db.query(Branch).filter(Branch.id == ver_a.branch_id).first()
    get_repository_by_id(db, branch_a.repository_id, current_user.id)

    text_diff = get_text_diff(ver_a.prompt_text, ver_b.prompt_text)
    config_diff = get_config_diff(
        ver_a.model_config or {},
        ver_b.model_config or {},
    )

    run_a = get_best_eval_run(db, version_a)
    run_b = get_best_eval_run(db, version_b)
    behavioral_diff = get_behavioral_diff(run_a, run_b)

    from app.models.user import User as UserModel
    author_a = db.query(UserModel).filter(UserModel.id == ver_a.author_id).first()
    author_b = db.query(UserModel).filter(UserModel.id == ver_b.author_id).first()

    return {
        "version_a": {
            "id": str(ver_a.id),
            "commit_message": ver_a.commit_message,
            "prompt_text": ver_a.prompt_text,
            "model_config": ver_a.model_config,
            "eval_score": ver_a.eval_score,
            "author_name": author_a.name if author_a else "Unknown",
            "created_at": ver_a.created_at.isoformat(),
        },
        "version_b": {
            "id": str(ver_b.id),
            "commit_message": ver_b.commit_message,
            "prompt_text": ver_b.prompt_text,
            "model_config": ver_b.model_config,
            "eval_score": ver_b.eval_score,
            "author_name": author_b.name if author_b else "Unknown",
            "created_at": ver_b.created_at.isoformat(),
        },
        "text_diff": text_diff,
        "config_diff": config_diff,
        "behavioral_diff": behavioral_diff,
    }