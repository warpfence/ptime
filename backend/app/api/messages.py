"""
채팅 메시지 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..services.message_service import get_message_service, MessageService
from ..schemas.message import (
    MessageResponse,
    MessageListResponse,
    MessageStats,
    MessageUpdate
)

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.get("/session/{session_id}", response_model=MessageListResponse)
async def get_session_messages(
    session_id: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서"),
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    세션의 채팅 메시지 목록 조회

    Args:
        session_id: 세션 ID
        page: 페이지 번호 (기본: 1)
        page_size: 페이지 크기 (기본: 50, 최대: 100)
        order: 정렬 순서 (asc/desc, 기본: desc)

    Returns:
        메시지 목록과 페이징 정보
    """
    try:
        result = await message_service.get_session_messages(
            db=db,
            session_id=session_id,
            page=page,
            page_size=page_size,
            order=order
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/session/{session_id}/recent")
async def get_recent_messages(
    session_id: str,
    limit: int = Query(20, ge=1, le=50, description="조회할 메시지 수"),
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    세션의 최근 메시지 조회 (캐시 우선)

    Args:
        session_id: 세션 ID
        limit: 조회할 메시지 수 (기본: 20, 최대: 50)

    Returns:
        최근 메시지 목록
    """
    try:
        messages = await message_service.get_recent_messages(
            db=db,
            session_id=session_id,
            limit=limit
        )
        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최근 메시지 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    메시지 단건 조회

    Args:
        message_id: 메시지 ID

    Returns:
        메시지 정보
    """
    try:
        message = await message_service.get_message(db=db, message_id=message_id)
        if not message:
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    update_data: MessageUpdate,
    participant_id: str = Query(..., description="참여자 ID"),
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    메시지 수정 (자신의 메시지만 수정 가능)

    Args:
        message_id: 메시지 ID
        update_data: 수정할 데이터
        participant_id: 참여자 ID

    Returns:
        수정된 메시지 정보
    """
    try:
        updated_message = await message_service.update_message(
            db=db,
            message_id=message_id,
            participant_id=participant_id,
            update_data=update_data
        )

        if not updated_message:
            raise HTTPException(
                status_code=404,
                detail="메시지를 찾을 수 없거나 수정 권한이 없습니다."
            )

        return updated_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    participant_id: str = Query(..., description="참여자 ID"),
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    메시지 삭제 (자신의 메시지만 삭제 가능)

    Args:
        message_id: 메시지 ID
        participant_id: 참여자 ID

    Returns:
        삭제 결과
    """
    try:
        success = await message_service.delete_message(
            db=db,
            message_id=message_id,
            participant_id=participant_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="메시지를 찾을 수 없거나 삭제 권한이 없습니다."
            )

        return {"message": "메시지가 성공적으로 삭제되었습니다.", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 삭제 중 오류가 발생했습니다: {str(e)}")


@router.get("/session/{session_id}/stats", response_model=MessageStats)
async def get_message_stats(
    session_id: str,
    db: Session = Depends(get_db),
    message_service: MessageService = Depends(get_message_service)
):
    """
    세션의 메시지 통계 조회

    Args:
        session_id: 세션 ID

    Returns:
        메시지 통계 정보
    """
    try:
        stats = await message_service.get_message_stats(db=db, session_id=session_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/session/{session_id}/clear")
async def clear_session_messages(
    session_id: str,
    confirm: bool = Query(False, description="삭제 확인"),
    db: Session = Depends(get_db)
):
    """
    세션의 모든 메시지 삭제 (관리자 기능)

    Args:
        session_id: 세션 ID
        confirm: 삭제 확인 (true여야 실행됨)

    Returns:
        삭제 결과
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="삭제를 실행하려면 confirm=true를 설정하세요.")

    try:
        # 실제 구현에서는 관리자 권한 확인 필요
        from ..models.message import Message

        # 소프트 삭제 처리
        db.query(Message).filter(
            Message.session_id == session_id,
            Message.is_deleted == False
        ).update({
            "is_deleted": True,
            "deleted_at": func.now()
        })

        db.commit()

        return {
            "message": f"세션 {session_id}의 모든 메시지가 삭제되었습니다.",
            "session_id": session_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"메시지 삭제 중 오류가 발생했습니다: {str(e)}")


@router.get("/health")
async def message_api_health():
    """메시지 API 헬스체크"""
    return {
        "status": "healthy",
        "service": "message_api",
        "timestamp": datetime.utcnow().isoformat()
    }