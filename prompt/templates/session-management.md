# 세션 관리 템플릿

## 1. 세션 스키마

### app/schemas/session.py
```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
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
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SessionResponse(BaseModel):
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
```

## 2. 세션 서비스

### app/services/session.py
```python
import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.session import Session as SessionModel
from ..models.participant import Participant
from ..schemas.session import SessionCreate, SessionUpdate
from .qr_code import QRCodeService

class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.qr_service = QRCodeService()

    def generate_session_code(self) -> str:
        """6자리 고유 세션 코드 생성"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if not self.db.query(SessionModel).filter(SessionModel.session_code == code).first():
                return code

    def create_session(self, user_id: str, session_data: SessionCreate) -> SessionModel:
        session = SessionModel(
            presenter_id=user_id,
            title=session_data.title,
            description=session_data.description,
            session_code=self.generate_session_code()
        )

        # QR 코드 생성
        session.qr_code_url = self.qr_service.generate_qr_code(session.session_code)

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_user_sessions(self, user_id: str) -> list[SessionModel]:
        return self.db.query(SessionModel).filter(
            SessionModel.presenter_id == user_id
        ).order_by(SessionModel.created_at.desc()).all()

    def get_session_by_id(self, session_id: str) -> SessionModel:
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_session_by_code(self, session_code: str) -> SessionModel:
        return self.db.query(SessionModel).filter(SessionModel.session_code == session_code).first()

    def update_session(self, session_id: str, session_data: SessionUpdate) -> SessionModel:
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        for field, value in session_data.dict(exclude_unset=True).items():
            setattr(session, field, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    def activate_session(self, session_id: str) -> SessionModel:
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.is_active = True
        session.started_at = func.now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def deactivate_session(self, session_id: str) -> SessionModel:
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.is_active = False
        session.ended_at = func.now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_participant_count(self, session_id: str) -> int:
        return self.db.query(Participant).filter(
            Participant.session_id == session_id
        ).count()
```

## 3. QR 코드 서비스

### app/services/qr_code.py
```python
import qrcode
import io
import base64
from typing import Optional
from ..config import settings

class QRCodeService:
    def __init__(self):
        self.base_url = getattr(settings, 'base_url', 'http://localhost:3000')

    def generate_qr_code(self, session_code: str) -> str:
        """세션 참여 URL QR 코드 생성"""
        url = f"{self.base_url}/join/{session_code}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Base64로 인코딩
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def generate_short_url(self, session_code: str) -> str:
        """단축 URL 생성"""
        return f"{self.base_url}/join/{session_code}"
```

## 4. 세션 API 라우터

### app/api/sessions.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..schemas.session import SessionCreate, SessionUpdate, SessionResponse
from ..services.session import SessionService

router = APIRouter()

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.create_session(str(current_user.id), session_data)
    return session

@router.get("/", response_model=List[SessionResponse])
def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    sessions = service.get_user_sessions(str(current_user.id))

    # 참여자 수 추가
    for session in sessions:
        session.participant_count = service.get_session_participant_count(str(session.id))

    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.get_session_by_id(session_id)

    if not session or session.presenter_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    session.participant_count = service.get_session_participant_count(session_id)
    return session

@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.get_session_by_id(session_id)

    if not session or session.presenter_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    updated_session = service.update_session(session_id, session_data)
    updated_session.participant_count = service.get_session_participant_count(session_id)
    return updated_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.get_session_by_id(session_id)

    if not session or session.presenter_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    if not service.delete_session(session_id):
        raise HTTPException(status_code=400, detail="Failed to delete session")

@router.post("/{session_id}/activate", response_model=SessionResponse)
def activate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.get_session_by_id(session_id)

    if not session or session.presenter_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    activated_session = service.activate_session(session_id)
    activated_session.participant_count = service.get_session_participant_count(session_id)
    return activated_session

@router.post("/{session_id}/deactivate", response_model=SessionResponse)
def deactivate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SessionService(db)
    session = service.get_session_by_id(session_id)

    if not session or session.presenter_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    deactivated_session = service.deactivate_session(session_id)
    deactivated_session.participant_count = service.get_session_participant_count(session_id)
    return deactivated_session
```