from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Any


class ModelConfiguration(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_message: Optional[str] = None


class PromptVersionCreate(BaseModel):
    prompt_text: str
    llm_config: Any = Field(default=None)
    commit_message: str
    branch_id: UUID

    def get_config_dict(self) -> dict:
        if self.llm_config is None:
            return ModelConfiguration().model_dump()
        if isinstance(self.llm_config, dict):
            return self.llm_config
        return self.llm_config.model_dump()


class PromptVersionResponse(BaseModel):
    id: UUID
    branch_id: UUID
    prompt_text: str
    llm_config: Optional[dict] = None
    commit_message: str
    author_id: UUID
    author_name: Optional[str] = None
    eval_score: Optional[float] = None
    created_at: datetime
    version_number: Optional[int] = None

    model_config = {"from_attributes": True}