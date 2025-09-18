from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Poll(BaseModel):
    __tablename__ = "polls"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    title = Column(String(200), nullable=False)
    options = Column(JSON, nullable=False)  # ["옵션1", "옵션2", ...]
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="polls")
    responses = relationship("PollResponse", back_populates="poll")

class PollResponse(BaseModel):
    __tablename__ = "poll_responses"

    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    selected_option = Column(String(200), nullable=False)

    # Relationships
    poll = relationship("Poll", back_populates="responses")
    participant = relationship("Participant", back_populates="poll_responses")