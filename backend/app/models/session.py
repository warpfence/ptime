from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Session(BaseModel):
    __tablename__ = "sessions"

    presenter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_code = Column(String(10), unique=True, index=True, nullable=False)
    qr_code_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    presenter = relationship("User", back_populates="sessions")
    participants = relationship("Participant", back_populates="session")
    modules = relationship("Module", back_populates="session")
    chat_messages = relationship("ChatMessage", back_populates="session")
    qna_questions = relationship("QnAQuestion", back_populates="session")
    polls = relationship("Poll", back_populates="session")