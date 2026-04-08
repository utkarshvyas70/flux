from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    model_config = Column(JSON, nullable=False, default=dict)
    commit_message = Column(String, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    eval_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    branch = relationship("Branch", back_populates="versions", foreign_keys=[branch_id])
    author = relationship("User", back_populates="prompt_versions")
    eval_runs = relationship("EvalRun", back_populates="version")