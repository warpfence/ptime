"""
참여자 관리 서비스
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from fastapi import HTTPException, status
from ..models.participant import Participant
from ..models.session import Session as SessionModel
from ..schemas.participant import ParticipantJoin
from datetime import datetime, timedelta


class ParticipantService:
    """참여자 관리 비즈니스 로직 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def join_session(
        self,
        session_code: str,
        participant_data: ParticipantJoin,
        ip_address: Optional[str] = None
    ) -> Participant:
        """
        세션에 참여자 추가

        Args:
            session_code: 세션 코드
            participant_data: 참여자 정보
            ip_address: 참여자 IP 주소

        Returns:
            생성된 참여자 객체

        Raises:
            HTTPException: 세션을 찾을 수 없거나 참여할 수 없는 경우
        """
        # 세션 조회
        session = self.db.query(SessionModel).filter(
            SessionModel.session_code == session_code.upper()
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="유효하지 않은 세션 코드입니다."
            )

        # 세션 활성화 상태 확인 (필요시)
        # if not session.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="현재 참여할 수 없는 세션입니다."
        #     )

        # 동일 세션 내 닉네임 중복 확인
        existing_participant = self.db.query(Participant).filter(
            and_(
                Participant.session_id == session.id,
                Participant.nickname == participant_data.nickname
            )
        ).first()

        if existing_participant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 닉네임입니다. 다른 닉네임을 선택해주세요."
            )

        # 참여자 생성
        participant = Participant(
            session_id=session.id,
            nickname=participant_data.nickname,
            ip_address=ip_address
        )

        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)

        return participant

    def get_session_participants(self, session_id: str) -> List[Participant]:
        """
        세션의 모든 참여자 조회

        Args:
            session_id: 세션 ID

        Returns:
            참여자 목록 (최신 참여 순)
        """
        return self.db.query(Participant).filter(
            Participant.session_id == session_id
        ).order_by(Participant.joined_at.desc()).all()

    def get_participant_by_id(self, participant_id: str) -> Optional[Participant]:
        """
        ID로 참여자 조회

        Args:
            participant_id: 참여자 ID

        Returns:
            참여자 객체 또는 None
        """
        return self.db.query(Participant).filter(
            Participant.id == participant_id
        ).first()

    def update_last_seen(self, participant_id: str) -> Optional[Participant]:
        """
        참여자 마지막 활동 시간 업데이트

        Args:
            participant_id: 참여자 ID

        Returns:
            업데이트된 참여자 객체 또는 None
        """
        participant = self.get_participant_by_id(participant_id)
        if not participant:
            return None

        participant.last_seen = func.now()
        self.db.commit()
        self.db.refresh(participant)

        return participant

    def remove_participant(self, participant_id: str) -> bool:
        """
        참여자 제거

        Args:
            participant_id: 참여자 ID

        Returns:
            제거 성공 여부
        """
        participant = self.get_participant_by_id(participant_id)
        if not participant:
            return False

        self.db.delete(participant)
        self.db.commit()
        return True

    def get_participant_count(self, session_id: str) -> int:
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

    def get_online_participants(
        self,
        session_id: str,
        threshold_minutes: int = 5
    ) -> List[Participant]:
        """
        온라인 참여자 조회 (최근 활동 기준)

        Args:
            session_id: 세션 ID
            threshold_minutes: 온라인으로 간주할 비활성 시간 (분)

        Returns:
            온라인 참여자 목록
        """
        threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)

        return self.db.query(Participant).filter(
            and_(
                Participant.session_id == session_id,
                Participant.last_seen >= threshold_time
            )
        ).all()

    def cleanup_inactive_participants(
        self,
        session_id: str,
        inactive_hours: int = 24
    ) -> int:
        """
        비활성 참여자 정리

        Args:
            session_id: 세션 ID
            inactive_hours: 비활성 기준 시간 (시간)

        Returns:
            정리된 참여자 수
        """
        threshold_time = datetime.utcnow() - timedelta(hours=inactive_hours)

        inactive_participants = self.db.query(Participant).filter(
            and_(
                Participant.session_id == session_id,
                Participant.last_seen < threshold_time
            )
        ).all()

        count = len(inactive_participants)
        for participant in inactive_participants:
            self.db.delete(participant)

        self.db.commit()
        return count

    def get_participant_by_nickname(
        self,
        session_id: str,
        nickname: str
    ) -> Optional[Participant]:
        """
        닉네임으로 참여자 조회

        Args:
            session_id: 세션 ID
            nickname: 닉네임

        Returns:
            참여자 객체 또는 None
        """
        return self.db.query(Participant).filter(
            and_(
                Participant.session_id == session_id,
                Participant.nickname == nickname
            )
        ).first()

    def check_nickname_availability(
        self,
        session_id: str,
        nickname: str
    ) -> bool:
        """
        닉네임 사용 가능 여부 확인

        Args:
            session_id: 세션 ID
            nickname: 확인할 닉네임

        Returns:
            사용 가능 여부 (True: 사용 가능, False: 이미 사용 중)
        """
        participant = self.get_participant_by_nickname(session_id, nickname)
        return participant is None