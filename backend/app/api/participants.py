"""
참여자 관리 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.participant import (
    ParticipantJoin,
    ParticipantResponse,
    ParticipantListResponse,
    ParticipantJoinResponse,
    ParticipantStats
)
from ..services.participant import ParticipantService
from ..services.session import SessionService

router = APIRouter(prefix="/api", tags=["참여자 관리"])


@router.post("/join/{session_code}", response_model=ParticipantJoinResponse)
def join_session(
    session_code: str,
    participant_data: ParticipantJoin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    세션 참여

    - **session_code**: 6자리 세션 코드
    - **nickname**: 참여자 닉네임 (1-20자)

    참여 시 자동으로:
    - 닉네임 중복 검사
    - IP 주소 기록
    - 참여 시간 기록
    """
    try:
        # IP 주소 추출
        client_ip = request.client.host
        if hasattr(request, 'headers') and 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()

        # 참여자 서비스
        participant_service = ParticipantService(db)
        participant = participant_service.join_session(
            session_code=session_code,
            participant_data=participant_data,
            ip_address=client_ip
        )

        # 세션 정보 조회
        session_service = SessionService(db)
        session = session_service.get_session_by_code(session_code.upper())

        # 응답 구성
        session_info = {
            "id": str(session.id),
            "title": session.title,
            "description": session.description,
            "is_active": session.is_active,
            "participant_count": participant_service.get_participant_count(str(session.id))
        }

        return ParticipantJoinResponse(
            message="세션에 성공적으로 참여했습니다.",
            participant=participant,
            session_info=session_info
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 참여 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sessions/{session_id}/participants", response_model=List[ParticipantListResponse])
def get_session_participants(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    세션 참여자 목록 조회

    세션의 모든 참여자를 최신 참여 순으로 반환합니다.
    각 참여자의 온라인 상태도 포함됩니다 (5분 이내 활동 기준).
    """
    try:
        participant_service = ParticipantService(db)

        # 세션 존재 확인
        session_service = SessionService(db)
        session = session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 참여자 목록 조회
        participants = participant_service.get_session_participants(session_id)
        online_participants = participant_service.get_online_participants(session_id)
        online_ids = {str(p.id) for p in online_participants}

        # 응답 구성
        participant_list = []
        for participant in participants:
            participant_dict = {
                "id": str(participant.id),
                "nickname": participant.nickname,
                "joined_at": participant.joined_at,
                "last_seen": participant.last_seen,
                "is_online": str(participant.id) in online_ids
            }
            participant_list.append(ParticipantListResponse(**participant_dict))

        return participant_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"참여자 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/participants/{participant_id}", response_model=ParticipantResponse)
def get_participant(
    participant_id: str,
    db: Session = Depends(get_db)
):
    """
    참여자 정보 조회

    특정 참여자의 상세 정보를 반환합니다.
    """
    try:
        participant_service = ParticipantService(db)
        participant = participant_service.get_participant_by_id(participant_id)

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="참여자를 찾을 수 없습니다."
            )

        return participant

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"참여자 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/participants/{participant_id}/activity")
def update_participant_activity(
    participant_id: str,
    db: Session = Depends(get_db)
):
    """
    참여자 활동 시간 업데이트

    참여자의 마지막 활동 시간을 현재 시간으로 업데이트합니다.
    WebSocket 연결이나 API 호출 시 주기적으로 호출하여 온라인 상태를 유지합니다.
    """
    try:
        participant_service = ParticipantService(db)
        participant = participant_service.update_last_seen(participant_id)

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="참여자를 찾을 수 없습니다."
            )

        return {"message": "활동 시간이 업데이트되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"활동 시간 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant(
    participant_id: str,
    db: Session = Depends(get_db)
):
    """
    참여자 제거

    세션에서 참여자를 제거합니다.
    참여자 본인이나 세션 관리자만 호출할 수 있습니다.
    """
    try:
        participant_service = ParticipantService(db)

        if not participant_service.remove_participant(participant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="참여자를 찾을 수 없습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"참여자 제거 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sessions/{session_id}/participants/stats", response_model=ParticipantStats)
def get_session_participant_stats(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    세션 참여자 통계

    세션의 참여자 통계 정보를 반환합니다.
    - 총 참여자 수
    - 온라인 참여자 수
    - 최근 참여자 수 (1시간 내)
    """
    try:
        participant_service = ParticipantService(db)

        # 세션 존재 확인
        session_service = SessionService(db)
        session = session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 통계 수집
        total_participants = participant_service.get_participant_count(session_id)
        online_participants = len(participant_service.get_online_participants(session_id))

        # 최근 참여자 수 (1시간 내)
        from datetime import datetime, timedelta
        recent_threshold = datetime.utcnow() - timedelta(hours=1)
        all_participants = participant_service.get_session_participants(session_id)
        recent_joins = len([p for p in all_participants if p.joined_at >= recent_threshold])

        return ParticipantStats(
            total_participants=total_participants,
            online_participants=online_participants,
            recent_joins=recent_joins,
            average_duration=None  # 향후 계산 로직 추가
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"참여자 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sessions/{session_id}/participants/check-nickname/{nickname}")
def check_nickname_availability(
    session_id: str,
    nickname: str,
    db: Session = Depends(get_db)
):
    """
    닉네임 사용 가능 여부 확인

    특정 세션에서 닉네임의 사용 가능 여부를 확인합니다.
    참여 전 닉네임 중복 검사에 사용됩니다.
    """
    try:
        participant_service = ParticipantService(db)

        # 세션 존재 확인
        session_service = SessionService(db)
        session = session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        is_available = participant_service.check_nickname_availability(session_id, nickname)

        return {
            "nickname": nickname,
            "is_available": is_available,
            "message": "사용 가능한 닉네임입니다." if is_available else "이미 사용 중인 닉네임입니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"닉네임 확인 중 오류가 발생했습니다: {str(e)}"
        )