from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class MessageType(enum.Enum):
    TEXT = "text"
    EMOJI = "emoji"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=True)
    message = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)

    # Relationships
    session = relationship("Session", back_populates="chat_messages")
    participant = relationship("Participant", back_populates="chat_messages")