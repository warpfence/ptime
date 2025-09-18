"""
인증 관련 API 엔드포인트들
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    UserLogin, UserRegister, TokenResponse, PasswordChange,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    UserProfile, UserProfileUpdate
)
from ..core.security import JWTToken, PasswordHandler, generate_password_reset_token, verify_password_reset_token
from ..core.dependencies import get_current_active_user, verify_refresh_token
from ..core.validators import EmailValidator
from ..config import settings

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    사용자 회원가입

    Args:
        user_data: 회원가입 정보
        request: HTTP 요청 객체
        db: 데이터베이스 세션

    Returns:
        TokenResponse: 토큰 정보

    Raises:
        HTTPException: 이미 존재하는 이메일인 경우
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다."
        )

    # 사용자명 중복 확인 (사용자명이 제공된 경우)
    if user_data.username:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다."
            )

    # 새 사용자 생성
    hashed_password = PasswordHandler.hash_password(user_data.password)

    db_user = User(
        email=user_data.email,
        username=user_data.username,
        name=user_data.name,
        hashed_password=hashed_password,
        is_verified=not settings.require_email_verification  # 이메일 인증 필수 여부에 따라 설정
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 토큰 생성
    access_token = JWTToken.create_access_token(
        data={"sub": db_user.id, "email": db_user.email}
    )
    refresh_token = JWTToken.create_refresh_token(
        data={"sub": db_user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    사용자 로그인

    Args:
        user_credentials: 로그인 자격증명
        request: HTTP 요청 객체
        db: 데이터베이스 세션

    Returns:
        TokenResponse: 토큰 정보

    Raises:
        HTTPException: 로그인 실패 시
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == user_credentials.email).first()

    if not user or not PasswordHandler.verify_password(
        user_credentials.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 패스워드가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 활성화 상태 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다.",
        )

    # 이메일 인증 확인 (필요한 경우)
    if settings.require_email_verification and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 인증이 필요합니다.",
        )

    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 토큰 생성
    access_token = JWTToken.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token = JWTToken.create_refresh_token(
        data={"sub": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: dict = Depends(verify_refresh_token),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    토큰 갱신

    Args:
        payload: 리프레시 토큰 페이로드
        db: 데이터베이스 세션

    Returns:
        TokenResponse: 새로운 토큰 정보
    """
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없거나 비활성화된 사용자입니다.",
        )

    # 새 토큰 생성
    access_token = JWTToken.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token = JWTToken.create_refresh_token(
        data={"sub": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserProfile:
    """
    현재 사용자 정보 조회

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        UserProfile: 사용자 프로필 정보
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
        updated_at=current_user.updated_at.isoformat() if current_user.updated_at else ""
    )


@router.patch("/me", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProfile:
    """
    현재 사용자 정보 수정

    Args:
        profile_data: 수정할 프로필 정보
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        UserProfile: 수정된 사용자 프로필 정보
    """
    update_data = profile_data.dict(exclude_unset=True)

    # 사용자명 중복 확인
    if "username" in update_data and update_data["username"]:
        existing_user = db.query(User).filter(
            and_(
                User.username == update_data["username"],
                User.id != current_user.id
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다."
            )

    # 사용자 정보 업데이트
    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
        updated_at=current_user.updated_at.isoformat() if current_user.updated_at else ""
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    패스워드 변경

    Args:
        password_data: 패스워드 변경 정보
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        Dict[str, str]: 성공 메시지
    """
    # 현재 패스워드 확인
    if not PasswordHandler.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 패스워드가 올바르지 않습니다."
        )

    # 새 패스워드로 변경
    current_user.hashed_password = PasswordHandler.hash_password(
        password_data.new_password
    )
    current_user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "패스워드가 성공적으로 변경되었습니다."}


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    패스워드 재설정 요청

    Args:
        password_reset: 패스워드 재설정 요청 정보
        db: 데이터베이스 세션

    Returns:
        Dict[str, str]: 성공 메시지
    """
    user = db.query(User).filter(User.email == password_reset.email).first()

    # 보안을 위해 사용자가 존재하지 않아도 성공 메시지 반환
    if user:
        # 실제 구현에서는 여기서 이메일 발송 로직 추가
        reset_token = generate_password_reset_token(user.email)
        # TODO: 이메일 발송 서비스 연동
        # await send_password_reset_email(user.email, reset_token)

    return {"message": "패스워드 재설정 링크가 이메일로 발송되었습니다."}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    패스워드 재설정 확인

    Args:
        reset_data: 패스워드 재설정 확인 정보
        db: 데이터베이스 세션

    Returns:
        Dict[str, str]: 성공 메시지
    """
    email = verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않거나 만료된 토큰입니다."
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    # 패스워드 변경
    user.hashed_password = PasswordHandler.hash_password(reset_data.new_password)
    user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "패스워드가 성공적으로 재설정되었습니다."}