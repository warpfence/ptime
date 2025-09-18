# 데이터베이스 모델 및 스키마

## 1. 데이터베이스 연결 설정

### app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 2. 기본 모델 클래스

### app/models/base.py

```python
from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class BaseModel(Base):
    """모든 모델의 기본 클래스"""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
```

## 3. 데이터베이스 모델

### app/models/user.py

```python
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    google_id = Column(String(100), unique=True, index=True, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # 관계
    sessions = relationship("Session", back_populates="host", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="user", cascade="all, delete-orphan")
```

### app/models/session.py

```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel

class SessionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class Session(BaseModel):
    __tablename__ = "sessions"

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_code = Column(String(10), unique=True, index=True, nullable=False)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.DRAFT, nullable=False)
    max_participants = Column(Integer, default=100, nullable=False)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 관계
    host = relationship("User", back_populates="sessions")
    participants = relationship("Participant", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
```

### app/models/participant.py

```python
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Participant(BaseModel):
    __tablename__ = "participants"

    nickname = Column(String(50), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_online = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # 관계
    session = relationship("Session", back_populates="participants")
    user = relationship("User", back_populates="participants")
    messages = relationship("Message", back_populates="participant", cascade="all, delete-orphan")
```

### app/models/message.py

```python
from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel

class MessageType(str, enum.Enum):
    CHAT = "chat"
    QUESTION = "question"
    POLL_VOTE = "poll_vote"
    SYSTEM = "system"

class Message(BaseModel):
    __tablename__ = "messages"

    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.CHAT, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=True)

    # 관계
    session = relationship("Session", back_populates="messages")
    participant = relationship("Participant", back_populates="messages")
```

## 4. Pydantic 스키마

### app/schemas/user.py

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    google_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: uuid.UUID
    is_verified: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

### app/schemas/session.py

```python
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.session import SessionStatus
from app.schemas.user import UserResponse

class SessionBase(BaseModel):
    title: str
    description: Optional[str] = None
    max_participants: int = 100

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

    @validator('max_participants')
    def max_participants_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Max participants must be positive')
        return v

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SessionStatus] = None
    max_participants: Optional[int] = None

class SessionResponse(SessionBase):
    id: uuid.UUID
    session_code: str
    status: SessionStatus
    host_id: uuid.UUID
    host: UserResponse
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    id: uuid.UUID
    title: str
    session_code: str
    status: SessionStatus
    participant_count: int
    max_participants: int
    created_at: datetime

    class Config:
        from_attributes = True
```

### app/schemas/participant.py

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import uuid

class ParticipantBase(BaseModel):
    nickname: str

    @validator('nickname')
    def nickname_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Nickname cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Nickname must be at least 2 characters')
        return v.strip()

class ParticipantCreate(ParticipantBase):
    session_code: str

class ParticipantUpdate(BaseModel):
    nickname: Optional[str] = None
    is_online: Optional[bool] = None

class ParticipantResponse(ParticipantBase):
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    is_online: bool
    joined_at: datetime
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### app/schemas/message.py

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import uuid

from app.models.message import MessageType

class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.CHAT

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()

class MessageCreate(MessageBase):
    session_id: uuid.UUID

class MessageResponse(MessageBase):
    id: uuid.UUID
    session_id: uuid.UUID
    participant_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
```