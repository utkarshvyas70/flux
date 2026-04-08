import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.eval import EvalRun, EvalCase, EvalRunStatus, EvalType
from app.models.prompt_version import PromptVersion


def run_exact_eval(actual: str, expected: str) -> float:
    return 1.0 if actual.strip().lower() == expected.strip().lower() else 0.0


def run_similarity_eval(actual: str, expected: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([actual, expected])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return max(0.0, min(1.0, float(similarity)))
    except Exception as e:
        print(f"Similarity eval error: {e}")
        return 0.0


def run_llm_judge_eval(actual: str, expected: str, prompt_text: str) -> float:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        judge_prompt = f"""You are an impartial judge evaluating the quality of an AI assistant response.

Original prompt: {prompt_text[:500]}

Expected output: {expected}

Actual output: {actual}

Score the actual output from 0.0 to 1.0 based on:
- Semantic similarity to expected output (0.4 weight)
- Correctness and accuracy (0.4 weight)
- Completeness (0.2 weight)

Respond with ONLY a decimal number between 0.0 and 1.0. Nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": judge_prompt}],
            max_tokens=10,
            temperature=0,
        )
        score_str = response.choices[0].message.content.strip()
        return max(0.0, min(1.0, float(score_str)))
    except Exception as e:
        print(f"LLM judge eval error: {e}")
        return 0.0


def call_llm(prompt_text: str, llm_config: dict, input_text: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-placeholder":
        # No API key — return the input as-is for testing exact match
        return input_text.strip()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        messages = []
        system_msg = llm_config.get("system_message")
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        full_prompt = f"{prompt_text}\n\n{input_text}" if prompt_text else input_text
        messages.append({"role": "user", "content": full_prompt})
        response = client.chat.completions.create(
            model=llm_config.get("model", "gpt-4o-mini"),
            messages=messages,
            max_tokens=llm_config.get("max_tokens", 1000),
            temperature=llm_config.get("temperature", 0.7),
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM call error: {e}")
        return f"ERROR: {str(e)}"


def process_eval_run(run_id: str) -> None:
    db: Session = SessionLocal()
    try:
        run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
        if not run:
            return

        run.status = EvalRunStatus.running
        db.commit()

        version = db.query(PromptVersion).filter(
            PromptVersion.id == run.version_id
        ).first()
        cases = db.query(EvalCase).filter(
            EvalCase.suite_id == run.suite_id
        ).all()

        results = []
        scores = []

        for case in cases:
            actual_output = call_llm(
                version.prompt_text,
                version.model_config or {},
                case.input_text,
            )

            if case.eval_type == EvalType.exact:
                score = run_exact_eval(actual_output, case.expected_output)
            elif case.eval_type == EvalType.similarity:
                score = run_similarity_eval(actual_output, case.expected_output)
            elif case.eval_type == EvalType.llm_judge:
                score = run_llm_judge_eval(
                    actual_output, case.expected_output, version.prompt_text
                )
            else:
                score = 0.0

            scores.append(score)
            results.append({
                "case_id": str(case.id),
                "input_text": case.input_text,
                "expected_output": case.expected_output,
                "actual_output": actual_output,
                "eval_type": case.eval_type.value,
                "score": round(score, 4),
                "passed": score >= 0.7,
            })

        overall_score = (sum(scores) / len(scores) * 100) if scores else 0.0
        run.status = EvalRunStatus.completed
        run.overall_score = round(overall_score, 2)
        run.results = results
        db.commit()

        version.eval_score = round(overall_score, 2)
        db.commit()

    except Exception as e:
        print(f"Eval run error: {e}")
        try:
            run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
            if run:
                run.status = EvalRunStatus.failed
                db.commit()
        except Exception:
            pass
    finally:
        db.close()