from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid
import enum


class EvalType(str, enum.Enum):
    exact = "exact"
    similarity = "similarity"
    llm_judge = "llm_judge"


class EvalRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class EvalSuite(Base):
    __tablename__ = "eval_suites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    repository = relationship("Repository", back_populates="eval_suites")
    cases = relationship("EvalCase", back_populates="suite")
    runs = relationship("EvalRun", back_populates="suite")


class EvalCase(Base):
    __tablename__ = "eval_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("eval_suites.id"), nullable=False)
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    eval_type = Column(Enum(EvalType), nullable=False, default=EvalType.exact)

    suite = relationship("EvalSuite", back_populates="cases")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("eval_suites.id"), nullable=False)
    status = Column(Enum(EvalRunStatus), nullable=False, default=EvalRunStatus.pending)
    overall_score = Column(Float, nullable=True)
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    version = relationship("PromptVersion", back_populates="eval_runs")
    suite = relationship("EvalSuite", back_populates="runs")