"""
채팅 메시지 모델
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Message(Base):
    """채팅 메시지 모델"""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    participant_id = Column(String, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="user_message", nullable=False)  # user_message, system_message, announcement

    # 메타데이터
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(String(500), nullable=True)

    # 상태 관리
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    edit_count = Column(Integer, default=0, nullable=False)

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # 인덱스 추가
    __table_args__ = (
        Index('idx_message_session_created', 'session_id', 'created_at'),
        Index('idx_message_participant', 'participant_id', 'created_at'),
        Index('idx_message_type_session', 'message_type', 'session_id'),
        Index('idx_message_active', 'session_id', 'is_deleted', 'created_at'),
    )

    def to_dict(self):
        """메시지를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "nickname": self.nickname,
            "message": self.content,
            "type": self.message_type,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "is_edited": self.is_edited,
            "edit_count": self.edit_count,
            "is_deleted": self.is_deleted
        }

    def to_websocket_format(self):
        """WebSocket 전송용 포맷으로 변환"""
        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "nickname": self.nickname,
            "message": self.content,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "type": self.message_type
        }

    def __repr__(self):
        return f"<Message(id={self.id}, session_id={self.session_id}, participant_id={self.participant_id})>"