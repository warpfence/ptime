"""
세션 관련 Pydantic 스키마 정의
"""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    """세션 생성 요청 스키마"""
    title: str
    description: Optional[str] = None

    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('제목은 2글자 이상이어야 합니다.')
        if len(v.strip()) > 100:
            raise ValueError('제목은 100글자 이하여야 합니다.')
        return v.strip()


class SessionUpdate(BaseModel):
    """세션 수정 요청 스키마"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('제목은 2글자 이상이어야 합니다.')
            if len(v.strip()) > 100:
                raise ValueError('제목은 100글자 이하여야 합니다.')
            return v.strip()
        return v


class SessionResponse(BaseModel):
    """세션 응답 스키마"""
    id: str
    title: str
    description: Optional[str]
    session_code: str
    qr_code_url: Optional[str]
    is_active: bool
    participant_count: int = 0
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        orm_mode = True


class SessionListResponse(BaseModel):
    """세션 목록 응답 스키마"""
    id: str
    title: str
    description: Optional[str]
    session_code: str
    is_active: bool
    participant_count: int = 0
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        orm_mode = True


class SessionActivateResponse(BaseModel):
    """세션 활성화/비활성화 응답 스키마"""
    message: str
    session: SessionResponse