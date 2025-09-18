"""
OAuth 관련 Pydantic 스키마들
"""

from typing import Optional
from pydantic import BaseModel, HttpUrl, validator


class OAuthLoginRequest(BaseModel):
    """OAuth 로그인 요청 스키마"""
    redirect_url: Optional[HttpUrl] = None

    @validator('redirect_url')
    def validate_redirect_url(cls, v):
        if v:
            # 보안을 위해 허용된 도메인만 리다이렉트 허용
            allowed_domains = ["http://localhost:3000", "https://localhost:3000"]
            if str(v) not in allowed_domains and not any(str(v).startswith(domain) for domain in allowed_domains):
                raise ValueError('허용되지 않은 리다이렉트 URL입니다.')
        return v


class OAuthLoginResponse(BaseModel):
    """OAuth 로그인 응답 스키마"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth 콜백 요청 스키마"""
    code: str
    state: str
    error: Optional[str] = None
    error_description: Optional[str] = None

    @validator('error')
    def validate_error(cls, v):
        if v:
            raise ValueError(f'OAuth 인증 오류: {v}')
        return v


class GoogleUserInfo(BaseModel):
    """Google 사용자 정보 스키마"""
    id: str
    email: str
    verified_email: bool
    name: str
    given_name: str
    family_name: str
    picture: Optional[str] = None
    locale: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth 토큰 응답 스키마 (기존 TokenResponse와 동일하지만 OAuth 컨텍스트)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict  # 사용자 기본 정보


class OAuthAccountLink(BaseModel):
    """OAuth 계정 연동 스키마"""
    provider: str = "google"
    provider_user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_verified: bool = True  # OAuth 계정은 기본적으로 인증된 것으로 처리


class OAuthError(BaseModel):
    """OAuth 오류 응답 스키마"""
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None