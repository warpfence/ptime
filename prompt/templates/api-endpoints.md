# API 엔드포인트

## 1. 세션 관리 API

### app/api/v1/sessions.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse
)

router = APIRouter()

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """새 세션 생성"""
    session_service = SessionService(db)
    return session_service.create_session(session_data, current_user.id)

@router.get("/", response_model=List[SessionListResponse])
async def get_user_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """사용자의 세션 목록 조회"""
    session_service = SessionService(db)
    return session_service.get_user_sessions(current_user.id, skip=skip, limit=limit)

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """특정 세션 조회"""
    session_service = SessionService(db)
    session = session_service.get_session_by_id(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 세션 호스트인지 확인
    if session.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )

    return session

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: uuid.UUID,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """세션 정보 수정"""
    session_service = SessionService(db)
    return session_service.update_session(session_id, session_data, current_user.id)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """세션 삭제"""
    session_service = SessionService(db)
    session_service.delete_session(session_id, current_user.id)

@router.post("/{session_id}/start")
async def start_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """세션 시작"""
    session_service = SessionService(db)
    return session_service.start_session(session_id, current_user.id)

@router.post("/{session_id}/end")
async def end_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """세션 종료"""
    session_service = SessionService(db)
    return session_service.end_session(session_id, current_user.id)

@router.get("/code/{session_code}", response_model=SessionResponse)
async def get_session_by_code(
    session_code: str,
    db: Session = Depends(get_db)
):
    """세션 코드로 세션 조회 (공개 API)"""
    session_service = SessionService(db)
    session = session_service.get_session_by_code(session_code)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session
```

## 2. 참가자 관리 API

### app/api/v1/participants.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.participant_service import ParticipantService
from app.schemas.participant import (
    ParticipantCreate,
    ParticipantUpdate,
    ParticipantResponse
)

router = APIRouter()

@router.post("/join", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def join_session(
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = None  # 선택적 인증
):
    """세션에 참가"""
    participant_service = ParticipantService(db)
    user_id = current_user.id if current_user else None

    return participant_service.join_session(
        session_code=participant_data.session_code,
        nickname=participant_data.nickname,
        user_id=user_id
    )

@router.get("/session/{session_id}", response_model=List[ParticipantResponse])
async def get_session_participants(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    only_online: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """세션 참가자 목록 조회"""
    participant_service = ParticipantService(db)

    # 세션 호스트인지 확인
    if not participant_service.is_session_host(session_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view participants"
        )

    return participant_service.get_session_participants(
        session_id=session_id,
        skip=skip,
        limit=limit,
        only_online=only_online
    )

@router.put("/{participant_id}", response_model=ParticipantResponse)
async def update_participant(
    participant_id: uuid.UUID,
    participant_data: ParticipantUpdate,
    db: Session = Depends(get_db)
):
    """참가자 정보 수정"""
    participant_service = ParticipantService(db)
    return participant_service.update_participant(participant_id, participant_data)

@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_session(
    participant_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """세션 떠나기"""
    participant_service = ParticipantService(db)
    participant_service.leave_session(participant_id)

@router.post("/{participant_id}/kick")
async def kick_participant(
    participant_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """참가자 강제 퇴장 (호스트만 가능)"""
    participant_service = ParticipantService(db)

    participant = participant_service.get_participant_by_id(participant_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    # 세션 호스트인지 확인
    if not participant_service.is_session_host(participant.session_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to kick participants"
        )

    participant_service.kick_participant(participant_id)
    return {"message": "Participant kicked successfully"}
```

## 3. 메시지 관리 API

### app/api/v1/messages.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter()

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """메시지 전송 (인증 없이도 가능)"""
    message_service = MessageService(db)
    return message_service.send_message(message_data)

@router.get("/session/{session_id}", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    message_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """세션 메시지 목록 조회"""
    message_service = MessageService(db)
    return message_service.get_session_messages(
        session_id=session_id,
        skip=skip,
        limit=limit,
        message_type=message_type
    )

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """메시지 삭제 (호스트만 가능)"""
    message_service = MessageService(db)

    message = message_service.get_message_by_id(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # 세션 호스트인지 확인
    if not message_service.is_session_host(message.session_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete messages"
        )

    message_service.delete_message(message_id)
```

## 4. 서비스 클래스 예시

### app/services/session_service.py

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import random
import string

from app.models.session import Session as SessionModel, SessionStatus
from app.models.participant import Participant
from app.schemas.session import SessionCreate, SessionUpdate, SessionListResponse
from app.exceptions import NotFoundException, ValidationException, AuthorizationException

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_session_code(self) -> str:
        """고유한 세션 코드 생성"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            existing = self.db.query(SessionModel).filter(SessionModel.session_code == code).first()
            if not existing:
                return code

    def create_session(self, session_data: SessionCreate, host_id: uuid.UUID) -> SessionModel:
        """새 세션 생성"""
        session_code = self._generate_session_code()

        session = SessionModel(
            title=session_data.title,
            description=session_data.description,
            session_code=session_code,
            max_participants=session_data.max_participants,
            host_id=host_id
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: uuid.UUID) -> Optional[SessionModel]:
        """세션 ID로 조회"""
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_session_by_code(self, session_code: str) -> Optional[SessionModel]:
        """세션 코드로 조회"""
        return self.db.query(SessionModel).filter(SessionModel.session_code == session_code).first()

    def get_user_sessions(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[SessionListResponse]:
        """사용자의 세션 목록 조회"""
        sessions = self.db.query(
            SessionModel,
            func.count(Participant.id).label('participant_count')
        ).outerjoin(Participant).filter(
            SessionModel.host_id == user_id
        ).group_by(SessionModel.id).offset(skip).limit(limit).all()

        return [
            SessionListResponse(
                id=session.id,
                title=session.title,
                session_code=session.session_code,
                status=session.status,
                participant_count=participant_count,
                max_participants=session.max_participants,
                created_at=session.created_at
            )
            for session, participant_count in sessions
        ]

    def update_session(self, session_id: uuid.UUID, session_data: SessionUpdate, user_id: uuid.UUID) -> SessionModel:
        """세션 정보 수정"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise NotFoundException("Session not found")

        if session.host_id != user_id:
            raise AuthorizationException("Not authorized to update this session")

        update_data = session_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID):
        """세션 삭제"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise NotFoundException("Session not found")

        if session.host_id != user_id:
            raise AuthorizationException("Not authorized to delete this session")

        self.db.delete(session)
        self.db.commit()

    def start_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel:
        """세션 시작"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise NotFoundException("Session not found")

        if session.host_id != user_id:
            raise AuthorizationException("Not authorized to start this session")

        if session.status != SessionStatus.DRAFT:
            raise ValidationException("Session cannot be started")

        session.status = SessionStatus.ACTIVE
        self.db.commit()
        self.db.refresh(session)
        return session

    def end_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel:
        """세션 종료"""
        session = self.get_session_by_id(session_id)
        if not session:
            raise NotFoundException("Session not found")

        if session.host_id != user_id:
            raise AuthorizationException("Not authorized to end this session")

        if session.status not in [SessionStatus.ACTIVE, SessionStatus.PAUSED]:
            raise ValidationException("Session cannot be ended")

        session.status = SessionStatus.ENDED
        self.db.commit()
        self.db.refresh(session)
        return session
```