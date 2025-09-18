"""
FastAPI 의존성 주입을 위한 함수들
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from .security import JWTToken

security = HTTPBearer()


def get_current_user_from_token(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    JWT 토큰에서 현재 사용자 정보를 가져오는 의존성 함수

    Args:
        db: 데이터베이스 세션
        credentials: HTTP Bearer 토큰

    Returns:
        User: 현재 인증된 사용자

    Raises:
        HTTPException: 인증 실패 시
    """
    token = credentials.credentials

    # 토큰 디코드
    payload = JWTToken.decode_token(token)

    # 토큰 타입 검증
    if not JWTToken.verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 토큰 타입입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 ID 추출
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 활성화 상태 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user_from_token)
) -> User:
    """
    현재 활성화된 사용자를 가져오는 의존성 함수

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        User: 현재 활성화된 사용자

    Raises:
        HTTPException: 사용자가 비활성화된 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다."
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    현재 관리자 사용자를 가져오는 의존성 함수

    Args:
        current_user: 현재 활성화된 사용자

    Returns:
        User: 현재 관리자 사용자

    Raises:
        HTTPException: 관리자 권한이 없는 경우
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    선택적으로 현재 사용자를 가져오는 의존성 함수 (토큰이 없어도 오류 발생 안함)

    Args:
        db: 데이터베이스 세션
        credentials: HTTP Bearer 토큰 (선택적)

    Returns:
        Optional[User]: 인증된 사용자 또는 None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = JWTToken.decode_token(token)

        if not JWTToken.verify_token_type(payload, "access"):
            return None

        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None

    except Exception:
        return None


def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    리프레시 토큰을 검증하는 의존성 함수

    Args:
        credentials: HTTP Bearer 토큰

    Returns:
        dict: 디코드된 토큰 페이로드

    Raises:
        HTTPException: 토큰 검증 실패 시
    """
    token = credentials.credentials
    payload = JWTToken.decode_token(token)

    if not JWTToken.verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 토큰 타입입니다. 리프레시 토큰이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload