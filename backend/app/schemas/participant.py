"""
참여자 관련 Pydantic 스키마 정의
"""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class ParticipantJoin(BaseModel):
    """참여자 세션 참여 요청 스키마"""
    nickname: str

    @validator('nickname')
    def validate_nickname(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('닉네임은 1글자 이상이어야 합니다.')
        if len(v.strip()) > 20:
            raise ValueError('닉네임은 20글자 이하여야 합니다.')

        # 특수문자 및 금지어 검증
        prohibited_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        if any(char in v for char in prohibited_chars):
            raise ValueError('닉네임에 특수문자는 사용할 수 없습니다.')

        return v.strip()


class ParticipantResponse(BaseModel):
    """참여자 응답 스키마"""
    id: str
    session_id: str
    nickname: str
    ip_address: Optional[str]
    joined_at: datetime
    last_seen: datetime

    class Config:
        orm_mode = True


class ParticipantListResponse(BaseModel):
    """참여자 목록 응답 스키마"""
    id: str
    nickname: str
    joined_at: datetime
    last_seen: datetime
    is_online: bool = True  # 실시간 상태 (향후 WebSocket으로 관리)

    class Config:
        orm_mode = True


class ParticipantJoinResponse(BaseModel):
    """참여자 세션 참여 성공 응답 스키마"""
    message: str
    participant: ParticipantResponse
    session_info: dict  # 세션의 기본 정보


class ParticipantStats(BaseModel):
    """참여자 통계 스키마"""
    total_participants: int
    online_participants: int
    recent_joins: int
    average_duration: Optional[float]  # 평균 참여 시간 (분)