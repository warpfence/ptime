"""
OAuth 인증 관련 API 엔드포인트들
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.oauth import (
    OAuthLoginRequest, OAuthLoginResponse,
    OAuthTokenResponse, GoogleUserInfo
)
from ..schemas.auth import TokenResponse
from ..core.oauth import google_oauth, oauth_session_manager
from ..core.security import JWTToken, PasswordHandler
from ..core.dependencies import get_current_active_user
from ..config import settings

router = APIRouter(prefix="/auth", tags=["OAuth 인증"])


@router.get("/login/google", response_model=OAuthLoginResponse)
async def google_login_start(
    redirect_url: str = Query(None, description="로그인 완료 후 리다이렉트할 URL")
) -> OAuthLoginResponse:
    """
    Google OAuth 로그인 시작

    Args:
        redirect_url: 로그인 완료 후 리다이렉트할 URL (선택사항)

    Returns:
        OAuthLoginResponse: Google 인증 URL과 state

    Raises:
        HTTPException: OAuth 설정이 되지 않은 경우
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth 서비스를 사용할 수 없습니다. 관리자에게 문의해주세요."
        )

    # 개발용 임시 처리: 실제 Google OAuth 설정이 없을 때
    if settings.google_client_id.startswith("test-") or settings.google_client_id == "your-google-client-id.apps.googleusercontent.com":
        # 개발용 mock 응답
        return OAuthLoginResponse(
            authorization_url="https://accounts.google.com/oauth/authorize?client_id=mock&redirect_uri=mock&response_type=code&scope=openid%20email%20profile&state=mock_state",
            state="mock_state"
        )

    # PKCE와 state 생성
    state = google_oauth.generate_state()
    code_verifier, code_challenge = google_oauth.generate_pkce_challenge()

    # 세션에 OAuth 정보 저장
    oauth_session_manager.create_session(
        state=state,
        code_verifier=code_verifier,
        redirect_url=redirect_url
    )

    # Google 인증 URL 생성
    authorization_url = google_oauth.get_authorization_url(state, code_challenge)

    return OAuthLoginResponse(
        authorization_url=authorization_url,
        state=state
    )


@router.get("/callback/google")
async def google_oauth_callback(
    code: str = Query(..., description="Google에서 받은 인증 코드"),
    state: str = Query(..., description="CSRF 보호를 위한 state 파라미터"),
    error: str = Query(None, description="OAuth 오류"),
    error_description: str = Query(None, description="OAuth 오류 설명"),
    db: Session = Depends(get_db)
):
    """
    Google OAuth 콜백 처리

    Args:
        code: Google에서 받은 인증 코드
        state: CSRF 보호를 위한 state 파라미터
        error: OAuth 오류 (있는 경우)
        error_description: OAuth 오류 설명
        db: 데이터베이스 세션

    Returns:
        RedirectResponse 또는 TokenResponse:
        - 프론트엔드 리다이렉트 또는 직접 토큰 반환

    Raises:
        HTTPException: 인증 실패 시
    """
    # OAuth 오류 처리
    if error:
        oauth_session_manager.remove_session(state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth 인증 실패: {error_description or error}"
        )

    # 세션에서 OAuth 정보 조회
    session_data = oauth_session_manager.get_session(state)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 OAuth 세션입니다. 다시 로그인을 시도해주세요."
        )

    code_verifier = session_data["code_verifier"]
    redirect_url = session_data.get("redirect_url")

    try:
        # 인증 코드를 액세스 토큰으로 교환
        token_data = await google_oauth.exchange_code_for_token(code, code_verifier)
        access_token = token_data["access_token"]

        # Google에서 사용자 정보 조회
        google_user_info = await google_oauth.get_user_info(access_token)

        # 데이터베이스에서 사용자 조회 또는 생성
        user = await get_or_create_oauth_user(db, google_user_info)

        # JWT 토큰 생성
        our_access_token = JWTToken.create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        refresh_token = JWTToken.create_refresh_token(
            data={"sub": user.id}
        )

        # 세션 정리
        oauth_session_manager.remove_session(state)

        # 리다이렉트 URL이 있으면 프론트엔드로 리다이렉트
        if redirect_url:
            # 토큰을 URL 파라미터로 전달 (실제 구현에서는 더 안전한 방법 사용 권장)
            redirect_with_tokens = f"{redirect_url}?access_token={our_access_token}&refresh_token={refresh_token}"
            return RedirectResponse(url=redirect_with_tokens)

        # 직접 토큰 반환
        return TokenResponse(
            access_token=our_access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    except Exception as e:
        oauth_session_manager.remove_session(state)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth 인증 처리 중 오류가 발생했습니다: {str(e)}"
        )


async def get_or_create_oauth_user(db: Session, google_user_info: Dict[str, Any]) -> User:
    """
    OAuth 사용자 정보로 기존 사용자 조회하거나 새 사용자 생성

    Args:
        db: 데이터베이스 세션
        google_user_info: Google에서 받은 사용자 정보

    Returns:
        User: 사용자 객체
    """
    email = google_user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 계정에서 이메일 정보를 가져올 수 없습니다."
        )

    # 이메일로 기존 사용자 조회
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        # 기존 사용자가 있으면 Google OAuth 정보 업데이트
        existing_user.google_id = google_user_info.get("id")
        existing_user.is_verified = True  # OAuth 계정은 자동으로 인증된 것으로 처리
        existing_user.last_login_at = datetime.utcnow()

        # 프로필 이미지가 없으면 Google 프로필 이미지 사용
        if not existing_user.profile_image and google_user_info.get("picture"):
            existing_user.profile_image = google_user_info["picture"]

        db.commit()
        db.refresh(existing_user)
        return existing_user

    # 새 사용자 생성
    # OAuth 사용자는 비밀번호가 없으므로 랜덤 해시 생성
    random_password = PasswordHandler.hash_password("oauth_user_no_password")

    new_user = User(
        email=email,
        name=google_user_info.get("name", ""),
        username=None,  # OAuth 사용자는 별도로 username 설정 가능
        hashed_password=random_password,
        google_id=google_user_info.get("id"),
        profile_image=google_user_info.get("picture"),
        is_active=True,
        is_verified=True,  # OAuth 계정은 자동으로 인증된 것으로 처리
        created_via_oauth=True,
        last_login_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/unlink/google")
async def unlink_google_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Google 계정 연동 해제

    Args:
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        Dict[str, str]: 성공 메시지

    Raises:
        HTTPException: 연동 해제 실패 시
    """
    if not current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 계정이 연동되어 있지 않습니다."
        )

    # OAuth로만 가입한 사용자는 연동 해제 전에 비밀번호 설정 필요
    if current_user.created_via_oauth and not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 계정 연동을 해제하기 전에 비밀번호를 설정해주세요."
        )

    # Google 연동 정보 제거
    current_user.google_id = None
    current_user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Google 계정 연동이 해제되었습니다."}