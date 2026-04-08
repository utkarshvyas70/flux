from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
import json
import time
import os
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.prompt_version import PromptVersion
from app.models.branch import Branch
from app.services.repository_service import get_repository_by_id

router = APIRouter(tags=["playground"])


class PlaygroundRequest(BaseModel):
    input_text: str
    model_override: Optional[str] = None


def generate_stream(
    prompt_text: str,
    llm_config: dict,
    input_text: str,
    model_override: Optional[str],
):
    api_key = os.getenv("OPENAI_API_KEY", "")
    start_time = time.time()

    if not api_key or api_key == "sk-placeholder":
        # No API key — simulate streaming for demo purposes
        demo_response = f"[Demo mode — no OpenAI key] You asked: {input_text}\n\nThis is a simulated streaming response. Add your OpenAI API key to enable real LLM inference."
        words = demo_response.split(" ")
        prompt_tokens = len(prompt_text.split()) + len(input_text.split())
        completion_tokens = len(words)

        for i, word in enumerate(words):
            chunk = {
                "type": "token",
                "content": word + (" " if i < len(words) - 1 else ""),
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            time.sleep(0.05)

        latency = round((time.time() - start_time) * 1000)
        final = {
            "type": "done",
            "latency_ms": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model_override or llm_config.get("model", "gpt-4o-mini"),
        }
        yield f"data: {json.dumps(final)}\n\n"
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        messages = []
        system_msg = llm_config.get("system_message")
        if system_msg:
            messages.append({"role": "system", "content": system_msg})

        full_prompt = f"{prompt_text}\n\n{input_text}" if prompt_text else input_text
        messages.append({"role": "user", "content": full_prompt})

        model = model_override or llm_config.get("model", "gpt-4o-mini")

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=llm_config.get("max_tokens", 1000),
            temperature=llm_config.get("temperature", 0.7),
            stream=True,
            stream_options={"include_usage": True},
        )

        prompt_tokens = 0
        completion_tokens = 0

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                token_chunk = {"type": "token", "content": content}
                yield f"data: {json.dumps(token_chunk)}\n\n"

            if hasattr(chunk, "usage") and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

        latency = round((time.time() - start_time) * 1000)
        final = {
            "type": "done",
            "latency_ms": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model,
        }
        yield f"data: {json.dumps(final)}\n\n"

    except Exception as e:
        error_chunk = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_chunk)}\n\n"


@router.post("/versions/{version_id}/playground")
def playground(
    version_id: UUID,
    data: PlaygroundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    branch = db.query(Branch).filter(Branch.id == version.branch_id).first()
    get_repository_by_id(db, branch.repository_id, current_user.id)

    return StreamingResponse(
        generate_stream(
            version.prompt_text,
            version.model_config or {},
            data.input_text,
            data.model_override,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )