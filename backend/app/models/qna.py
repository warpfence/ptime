from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class QnAQuestion(BaseModel):
    __tablename__ = "qna_questions"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    vote_count = Column(Integer, default=0)
    is_answered = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="qna_questions")
    participant = relationship("Participant", back_populates="qna_questions")