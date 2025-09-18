"""
보안 및 JWT 토큰 관련 유틸리티 함수들
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..config import settings

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTToken:
    """JWT 토큰 관리 클래스"""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        액세스 토큰 생성

        Args:
            data: 토큰에 포함할 데이터 (일반적으로 user_id, email 등)
            expires_delta: 토큰 만료 시간 (기본값: 설정파일의 값 사용)

        Returns:
            str: JWT 토큰 문자열
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        리프레시 토큰 생성 (7일 만료)

        Args:
            data: 토큰에 포함할 데이터

        Returns:
            str: JWT 리프레시 토큰
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        JWT 토큰 디코드 및 검증

        Args:
            token: JWT 토큰 문자열

        Returns:
            Dict[str, Any]: 디코드된 토큰 데이터

        Raises:
            HTTPException: 토큰 검증 실패 시
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 검증에 실패했습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
        """
        토큰 타입 검증

        Args:
            payload: 디코드된 토큰 데이터
            expected_type: 예상되는 토큰 타입 ('access' or 'refresh')

        Returns:
            bool: 토큰 타입이 일치하는지 여부
        """
        return payload.get("type") == expected_type


class PasswordHandler:
    """패스워드 해싱 및 검증 클래스"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        패스워드 해싱

        Args:
            password: 원본 패스워드

        Returns:
            str: 해싱된 패스워드
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        패스워드 검증

        Args:
            plain_password: 입력된 원본 패스워드
            hashed_password: 저장된 해싱된 패스워드

        Returns:
            bool: 패스워드 일치 여부
        """
        return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token(email: str) -> str:
    """
    패스워드 재설정 토큰 생성 (1시간 만료)

    Args:
        email: 사용자 이메일

    Returns:
        str: 패스워드 재설정 토큰
    """
    delta = timedelta(hours=1)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    패스워드 재설정 토큰 검증

    Args:
        token: 패스워드 재설정 토큰

    Returns:
        Optional[str]: 검증 성공 시 이메일, 실패 시 None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        if decoded_token.get("type") != "password_reset":
            return None
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """
    이메일 인증 토큰 생성 (24시간 만료)

    Args:
        email: 사용자 이메일

    Returns:
        str: 이메일 인증 토큰
    """
    delta = timedelta(hours=24)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "email_verification"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    이메일 인증 토큰 검증

    Args:
        token: 이메일 인증 토큰

    Returns:
        Optional[str]: 검증 성공 시 이메일, 실패 시 None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        if decoded_token.get("type") != "email_verification":
            return None
        return decoded_token["sub"]
    except jwt.JWTError:
        return None