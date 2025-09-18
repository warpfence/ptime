from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # OAuth 사용자는 NULL 가능

    # OAuth 관련 필드
    google_id = Column(String(255), unique=True, nullable=True)
    profile_image = Column(String(500), nullable=True)
    created_via_oauth = Column(Boolean, default=False)

    # 계정 상태
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # 타임스탬프
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="presenter")