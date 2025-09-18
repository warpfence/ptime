"""
OAuth 인증 관련 유틸리티 함수들
"""

import secrets
import base64
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import httpx
from fastapi import HTTPException, status
from ..config import settings


class GoogleOAuth:
    """Google OAuth 인증 클래스"""

    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

        # Google OAuth URLs
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def generate_state(self) -> str:
        """
        OAuth state 파라미터 생성 (CSRF 보호)

        Returns:
            str: 랜덤 state 문자열
        """
        return secrets.token_urlsafe(32)

    def generate_pkce_challenge(self) -> tuple[str, str]:
        """
        PKCE (Proof Key for Code Exchange) 챌린지 생성

        Returns:
            tuple[str, str]: (code_verifier, code_challenge)
        """
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """
        Google OAuth 인증 URL 생성

        Args:
            state: CSRF 보호를 위한 state 파라미터
            code_challenge: PKCE code challenge

        Returns:
            str: Google OAuth 인증 URL
        """
        if not self.client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth가 구성되지 않았습니다."
            )

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent"
        }

        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """
        인증 코드를 액세스 토큰으로 교환

        Args:
            code: Google에서 받은 인증 코드
            code_verifier: PKCE code verifier

        Returns:
            Dict[str, Any]: 토큰 정보

        Raises:
            HTTPException: 토큰 교환 실패 시
        """
        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth가 구성되지 않았습니다."
            )

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"토큰 교환에 실패했습니다: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth 토큰 교환 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Google 사용자 정보 조회

        Args:
            access_token: Google 액세스 토큰

        Returns:
            Dict[str, Any]: 사용자 정보

        Raises:
            HTTPException: 사용자 정보 조회 실패 시
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.userinfo_url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"사용자 정보 조회에 실패했습니다: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}"
            )

    def verify_state(self, received_state: str, expected_state: str) -> bool:
        """
        OAuth state 검증

        Args:
            received_state: 받은 state
            expected_state: 예상 state

        Returns:
            bool: state 일치 여부
        """
        return secrets.compare_digest(received_state, expected_state)


class OAuthSessionManager:
    """OAuth 세션 관리 클래스"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, state: str, code_verifier: str, redirect_url: Optional[str] = None) -> None:
        """
        OAuth 세션 생성

        Args:
            state: OAuth state
            code_verifier: PKCE code verifier
            redirect_url: 로그인 후 리다이렉트할 URL
        """
        self._sessions[state] = {
            "code_verifier": code_verifier,
            "redirect_url": redirect_url,
            "created_at": secrets.token_hex(16)  # 임시 타임스탬프 대용
        }

    def get_session(self, state: str) -> Optional[Dict[str, Any]]:
        """
        OAuth 세션 조회

        Args:
            state: OAuth state

        Returns:
            Optional[Dict[str, Any]]: 세션 정보 또는 None
        """
        return self._sessions.get(state)

    def remove_session(self, state: str) -> None:
        """
        OAuth 세션 제거

        Args:
            state: OAuth state
        """
        self._sessions.pop(state, None)

    def cleanup_expired_sessions(self) -> None:
        """
        만료된 세션 정리 (실제 구현에서는 Redis 등을 사용하여 TTL로 관리)
        """
        # 실제 구현에서는 Redis TTL이나 데이터베이스 타임스탬프로 관리
        pass


# 전역 인스턴스
google_oauth = GoogleOAuth()
oauth_session_manager = OAuthSessionManager()