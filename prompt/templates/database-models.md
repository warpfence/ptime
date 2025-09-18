# 데이터베이스 모델 템플릿

## 1. 기본 모델 클래스

### app/models/base.py
```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 2. 사용자 모델

### app/models/user.py
```python
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # google, email 등
    provider_id = Column(String(255), nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="presenter")
```

## 3. 세션 모델

### app/models/session.py
```python
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Session(BaseModel):
    __tablename__ = "sessions"

    presenter_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_code = Column(String(10), unique=True, index=True, nullable=False)
    qr_code_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    presenter = relationship("User", back_populates="sessions")
    participants = relationship("Participant", back_populates="session")
    modules = relationship("Module", back_populates="session")
    chat_messages = relationship("ChatMessage", back_populates="session")
    qna_questions = relationship("QnAQuestion", back_populates="session")
    polls = relationship("Poll", back_populates="session")
```

## 4. 참여자 모델

### app/models/participant.py
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import BaseModel

class Participant(BaseModel):
    __tablename__ = "participants"

    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    nickname = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="participants")
    chat_messages = relationship("ChatMessage", back_populates="participant")
    qna_questions = relationship("QnAQuestion", back_populates="participant")
    poll_responses = relationship("PollResponse", back_populates="participant")
```

## 5. 모듈 모델

### app/models/module.py
```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Module(BaseModel):
    __tablename__ = "modules"

    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    module_type = Column(String(50), nullable=False)  # chat, qna, poll, quiz
    module_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="modules")
```

## 6. 채팅 메시지 모델

### app/models/chat.py
```python
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class MessageType(enum.Enum):
    TEXT = "text"
    EMOJI = "emoji"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    participant_id = Column(UUID, ForeignKey("participants.id"), nullable=True)
    message = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)

    # Relationships
    session = relationship("Session", back_populates="chat_messages")
    participant = relationship("Participant", back_populates="chat_messages")
```

## 7. Q&A 모델

### app/models/qna.py
```python
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class QnAQuestion(BaseModel):
    __tablename__ = "qna_questions"

    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    participant_id = Column(UUID, ForeignKey("participants.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    vote_count = Column(Integer, default=0)
    is_answered = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="qna_questions")
    participant = relationship("Participant", back_populates="qna_questions")
```

## 8. 투표 모델

### app/models/poll.py
```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Poll(BaseModel):
    __tablename__ = "polls"

    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    title = Column(String(200), nullable=False)
    options = Column(JSON, nullable=False)  # ["옵션1", "옵션2", ...]
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="polls")
    responses = relationship("PollResponse", back_populates="poll")

class PollResponse(BaseModel):
    __tablename__ = "poll_responses"

    poll_id = Column(UUID, ForeignKey("polls.id"), nullable=False)
    participant_id = Column(UUID, ForeignKey("participants.id"), nullable=False)
    selected_option = Column(String(200), nullable=False)

    # Relationships
    poll = relationship("Poll", back_populates="responses")
    participant = relationship("Participant", back_populates="poll_responses")
```