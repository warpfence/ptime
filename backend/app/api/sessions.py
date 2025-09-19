"""
세션 관리 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..core.dependencies import get_current_active_user
from ..models.user import User
from ..schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionActivateResponse
)
from ..services.session import SessionService

router = APIRouter(prefix="/sessions", tags=["세션 관리"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    새 세션 생성

    - **title**: 세션 제목 (2-100자)
    - **description**: 세션 설명 (선택사항)

    세션 생성 시 자동으로:
    - 6자리 고유 세션 코드 생성
    - QR 코드 이미지 생성
    - 발표자로 현재 사용자 설정
    """
    try:
        service = SessionService(db)
        session = service.create_session(str(current_user.id), session_data)

        # 참여자 수 추가
        session.participant_count = service.get_session_participant_count(str(session.id))

        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=List[SessionListResponse])
def get_my_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    내가 생성한 세션 목록 조회

    최신 생성 순으로 정렬되어 반환됩니다.
    각 세션의 현재 참여자 수도 포함됩니다.
    """
    try:
        service = SessionService(db)
        sessions = service.get_user_sessions(str(current_user.id))

        # 각 세션에 참여자 수 추가
        for session in sessions:
            session.participant_count = service.get_session_participant_count(str(session.id))

        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 세션 상세 정보 조회

    본인이 생성한 세션만 조회할 수 있습니다.
    QR 코드 URL과 참여자 수 등 상세 정보가 포함됩니다.
    """
    try:
        service = SessionService(db)

        # 세션 존재 확인
        session = service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 소유권 확인
        if not service.check_session_ownership(session_id, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 세션에 접근할 권한이 없습니다."
            )

        # 참여자 수 추가
        session.participant_count = service.get_session_participant_count(session_id)

        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 정보 수정

    본인이 생성한 세션만 수정할 수 있습니다.
    - **title**: 세션 제목
    - **description**: 세션 설명
    - **is_active**: 활성화 상태
    """
    try:
        service = SessionService(db)

        # 세션 존재 및 소유권 확인
        if not service.check_session_ownership(session_id, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없거나 접근 권한이 없습니다."
            )

        # 세션 수정
        updated_session = service.update_session(session_id, session_data)
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 참여자 수 추가
        updated_session.participant_count = service.get_session_participant_count(session_id)

        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 삭제

    본인이 생성한 세션만 삭제할 수 있습니다.
    세션과 관련된 모든 데이터(참여자, 채팅 등)가 함께 삭제됩니다.
    """
    try:
        service = SessionService(db)

        # 세션 존재 및 소유권 확인
        if not service.check_session_ownership(session_id, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없거나 접근 권한이 없습니다."
            )

        # 세션 삭제
        if not service.delete_session(session_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="세션 삭제에 실패했습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{session_id}/activate", response_model=SessionActivateResponse)
def activate_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 활성화

    세션을 활성화하여 참여자들이 참여할 수 있도록 합니다.
    본인이 생성한 세션만 활성화할 수 있습니다.
    """
    try:
        service = SessionService(db)

        # 세션 존재 및 소유권 확인
        if not service.check_session_ownership(session_id, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없거나 접근 권한이 없습니다."
            )

        # 세션 활성화
        activated_session = service.activate_session(session_id)
        if not activated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 참여자 수 추가
        activated_session.participant_count = service.get_session_participant_count(session_id)

        return SessionActivateResponse(
            message="세션이 활성화되었습니다.",
            session=activated_session
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 활성화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{session_id}/deactivate", response_model=SessionActivateResponse)
def deactivate_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 비활성화

    세션을 종료하여 새로운 참여자 입장을 차단합니다.
    본인이 생성한 세션만 비활성화할 수 있습니다.
    """
    try:
        service = SessionService(db)

        # 세션 존재 및 소유권 확인
        if not service.check_session_ownership(session_id, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없거나 접근 권한이 없습니다."
            )

        # 세션 비활성화
        deactivated_session = service.deactivate_session(session_id)
        if not deactivated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 참여자 수 추가
        deactivated_session.participant_count = service.get_session_participant_count(session_id)

        return SessionActivateResponse(
            message="세션이 비활성화되었습니다.",
            session=deactivated_session
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 비활성화 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/code/{session_code}", response_model=SessionResponse)
def get_session_by_code(
    session_code: str,
    db: Session = Depends(get_db)
):
    """
    세션 코드로 세션 정보 조회 (공개)

    QR 코드 스캔이나 참여 링크 접속 시 사용됩니다.
    인증이 필요하지 않으며, 기본적인 세션 정보만 반환됩니다.
    """
    try:
        service = SessionService(db)
        session = service.get_session_by_code(session_code.upper())

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="유효하지 않은 세션 코드입니다."
            )

        # 참여자 수 추가
        session.participant_count = service.get_session_participant_count(str(session.id))

        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 조회 중 오류가 발생했습니다: {str(e)}"
        )