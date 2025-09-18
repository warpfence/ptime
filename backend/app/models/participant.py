from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Participant(BaseModel):
    __tablename__ = "participants"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    nickname = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="participants")
    chat_messages = relationship("ChatMessage", back_populates="participant")
    qna_questions = relationship("QnAQuestion", back_populates="participant")
    poll_responses = relationship("PollResponse", back_populates="participant")