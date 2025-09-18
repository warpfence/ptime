from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Module(BaseModel):
    __tablename__ = "modules"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    module_type = Column(String(50), nullable=False)  # chat, qna, poll, quiz
    module_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="modules")