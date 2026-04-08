from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class Branch(Base):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    name = Column(String, nullable=False)
    created_from_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    repository = relationship("Repository", back_populates="branches")
    versions = relationship("PromptVersion", back_populates="branch", foreign_keys="PromptVersion.branch_id")
    created_from_version = relationship("PromptVersion", foreign_keys=[created_from_version_id])