"""
세션 관리 서비스
"""

import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..models.session import Session as SessionModel
from ..models.participant import Participant
from ..schemas.session import SessionCreate, SessionUpdate
from .qr_code import QRCodeService


class SessionService:
    """세션 CRUD 비즈니스 로직 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.qr_service = QRCodeService()

    def generate_session_code(self) -> str:
        """
        6자리 고유 세션 코드 생성

        Returns:
            6자리 영숫자 대문자 세션 코드
        """
        while True:
            # 6자리 대문자 영숫자 코드 생성
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

            # 중복 확인
            existing = self.db.query(SessionModel).filter(SessionModel.session_code == code).first()
            if not existing:
                return code

    def create_session(self, user_id: str, session_data: SessionCreate) -> SessionModel:
        """
        새 세션 생성

        Args:
            user_id: 발표자 사용자 ID
            session_data: 세션 생성 데이터

        Returns:
            생성된 세션 객체
        """
        # 세션 코드 생성
        session_code = self.generate_session_code()

        # 세션 객체 생성
        session = SessionModel(
            presenter_id=user_id,
            title=session_data.title,
            description=session_data.description,
            session_code=session_code
        )

        # QR 코드 생성
        session.qr_code_url = self.qr_service.generate_qr_code(session_code)

        # 데이터베이스에 저장
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_user_sessions(self, user_id: str) -> List[SessionModel]:
        """
        사용자의 모든 세션 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자가 생성한 세션 목록 (최신순)
        """
        return self.db.query(SessionModel).filter(
            SessionModel.presenter_id == user_id
        ).order_by(SessionModel.created_at.desc()).all()

    def get_session_by_id(self, session_id: str) -> Optional[SessionModel]:
        """
        ID로 세션 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 객체 또는 None
        """
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_session_by_code(self, session_code: str) -> Optional[SessionModel]:
        """
        세션 코드로 세션 조회

        Args:
            session_code: 세션 코드

        Returns:
            세션 객체 또는 None
        """
        return self.db.query(SessionModel).filter(SessionModel.session_code == session_code).first()

    def update_session(self, session_id: str, session_data: SessionUpdate) -> Optional[SessionModel]:
        """
        세션 정보 수정

        Args:
            session_id: 세션 ID
            session_data: 수정할 데이터

        Returns:
            수정된 세션 객체 또는 None
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        # 변경된 필드만 업데이트
        update_data = session_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            삭제 성공 여부
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    def activate_session(self, session_id: str) -> Optional[SessionModel]:
        """
        세션 활성화

        Args:
            session_id: 세션 ID

        Returns:
            활성화된 세션 객체 또는 None
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.is_active = True
        session.started_at = func.now()

        self.db.commit()
        self.db.refresh(session)
        return session

    def deactivate_session(self, session_id: str) -> Optional[SessionModel]:
        """
        세션 비활성화

        Args:
            session_id: 세션 ID

        Returns:
            비활성화된 세션 객체 또는 None
        """
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.is_active = False
        session.ended_at = func.now()

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_participant_count(self, session_id: str) -> int:
        """
        세션 참여자 수 조회

        Args:
            session_id: 세션 ID

        Returns:
            참여자 수
        """
        return self.db.query(Participant).filter(
            Participant.session_id == session_id
        ).count()

    def check_session_ownership(self, session_id: str, user_id: str) -> bool:
        """
        세션 소유권 확인

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID

        Returns:
            소유권 확인 결과
        """
        session = self.get_session_by_id(session_id)
        return session is not None and str(session.presenter_id) == str(user_id)

    def get_active_sessions_count(self, user_id: str) -> int:
        """
        사용자의 활성 세션 수 조회

        Args:
            user_id: 사용자 ID

        Returns:
            활성 세션 수
        """
        return self.db.query(SessionModel).filter(
            SessionModel.presenter_id == user_id,
            SessionModel.is_active == True
        ).count()