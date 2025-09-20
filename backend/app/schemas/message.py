"""
채팅 메시지 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """메시지 타입"""
    USER_MESSAGE = "user_message"
    SYSTEM_MESSAGE = "system_message"
    ANNOUNCEMENT = "announcement"


class MessageCreate(BaseModel):
    """메시지 생성 스키마"""
    session_id: str = Field(..., min_length=1, max_length=100)
    participant_id: str = Field(..., min_length=1, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: MessageType = MessageType.USER_MESSAGE
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)

    @validator('content')
    def validate_content(cls, v):
        """메시지 내용 검증"""
        if not v.strip():
            raise ValueError('메시지 내용은 비어있을 수 없습니다.')

        # 금지된 문자 체크
        forbidden_chars = ['<script', '</script', 'javascript:', 'data:']
        content_lower = v.lower()
        for char in forbidden_chars:
            if char in content_lower:
                raise ValueError(f'금지된 문자가 포함되어 있습니다: {char}')

        return v.strip()

    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 검증"""
        if not v.strip():
            raise ValueError('닉네임은 비어있을 수 없습니다.')

        # 특수문자 검증
        prohibited_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        if any(char in v for char in prohibited_chars):
            raise ValueError('닉네임에 특수문자는 사용할 수 없습니다.')

        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "participant_id": "participant_456",
                "nickname": "사용자1",
                "content": "안녕하세요! 반갑습니다.",
                "message_type": "user_message"
            }
        }


class MessageUpdate(BaseModel):
    """메시지 수정 스키마"""
    content: str = Field(..., min_length=1, max_length=1000)

    @validator('content')
    def validate_content(cls, v):
        """메시지 내용 검증"""
        if not v.strip():
            raise ValueError('메시지 내용은 비어있을 수 없습니다.')

        # 금지된 문자 체크
        forbidden_chars = ['<script', '</script', 'javascript:', 'data:']
        content_lower = v.lower()
        for char in forbidden_chars:
            if char in content_lower:
                raise ValueError(f'금지된 문자가 포함되어 있습니다: {char}')

        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "content": "수정된 메시지 내용입니다."
            }
        }


class MessageResponse(BaseModel):
    """메시지 응답 스키마"""
    id: str
    session_id: str
    participant_id: str
    nickname: str
    message: str
    type: str
    timestamp: datetime
    is_edited: bool = False
    edit_count: int = 0
    is_deleted: bool = False

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "msg_12345",
                "session_id": "session_123",
                "participant_id": "participant_456",
                "nickname": "사용자1",
                "message": "안녕하세요! 반갑습니다.",
                "type": "user_message",
                "timestamp": "2023-12-01T10:30:00Z",
                "is_edited": False,
                "edit_count": 0,
                "is_deleted": False
            }
        }


class MessageListResponse(BaseModel):
    """메시지 목록 응답 스키마"""
    messages: List[MessageResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool

    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "msg_12345",
                        "session_id": "session_123",
                        "participant_id": "participant_456",
                        "nickname": "사용자1",
                        "message": "안녕하세요!",
                        "type": "user_message",
                        "timestamp": "2023-12-01T10:30:00Z",
                        "is_edited": False,
                        "edit_count": 0,
                        "is_deleted": False
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 50,
                "has_next": False
            }
        }


class WebSocketMessageData(BaseModel):
    """WebSocket 메시지 데이터 스키마"""
    id: str
    participant_id: str
    nickname: str
    message: str
    timestamp: str
    type: str = "user_message"

    class Config:
        schema_extra = {
            "example": {
                "id": "msg_12345",
                "participant_id": "participant_456",
                "nickname": "사용자1",
                "message": "안녕하세요!",
                "timestamp": "2023-12-01T10:30:00Z",
                "type": "user_message"
            }
        }


class MessageSendRequest(BaseModel):
    """WebSocket 메시지 전송 요청 스키마"""
    message: str = Field(..., min_length=1, max_length=1000)

    @validator('message')
    def validate_message(cls, v):
        """메시지 검증"""
        if not v.strip():
            raise ValueError('메시지는 비어있을 수 없습니다.')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "message": "안녕하세요! 반갑습니다."
            }
        }


class MessageStats(BaseModel):
    """메시지 통계 스키마"""
    session_id: str
    total_messages: int
    total_participants: int
    messages_per_participant: float
    first_message_at: Optional[datetime]
    last_message_at: Optional[datetime]

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "total_messages": 150,
                "total_participants": 25,
                "messages_per_participant": 6.0,
                "first_message_at": "2023-12-01T10:00:00Z",
                "last_message_at": "2023-12-01T12:30:00Z"
            }
        }