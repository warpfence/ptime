"""
입력 검증 및 보안 관련 유틸리티 함수들
"""

import re
from typing import List
from fastapi import HTTPException, status
from ..config import settings


class PasswordValidator:
    """패스워드 검증 클래스"""

    @staticmethod
    def validate_password(password: str) -> List[str]:
        """
        패스워드 강도 검증

        Args:
            password: 검증할 패스워드

        Returns:
            List[str]: 검증 실패 메시지 리스트 (빈 리스트면 검증 통과)
        """
        errors = []

        # 최소 길이 검증
        if len(password) < settings.password_min_length:
            errors.append(f"패스워드는 최소 {settings.password_min_length}자 이상이어야 합니다.")

        # 대문자 포함 검증
        if not re.search(r'[A-Z]', password):
            errors.append("패스워드는 대문자를 포함해야 합니다.")

        # 소문자 포함 검증
        if not re.search(r'[a-z]', password):
            errors.append("패스워드는 소문자를 포함해야 합니다.")

        # 숫자 포함 검증
        if not re.search(r'\d', password):
            errors.append("패스워드는 숫자를 포함해야 합니다.")

        # 특수문자 포함 검증
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("패스워드는 특수문자를 포함해야 합니다.")

        # 공백 검증
        if ' ' in password:
            errors.append("패스워드에는 공백을 포함할 수 없습니다.")

        return errors

    @staticmethod
    def is_strong_password(password: str) -> bool:
        """
        패스워드 강도 확인

        Args:
            password: 확인할 패스워드

        Returns:
            bool: 강력한 패스워드 여부
        """
        return len(PasswordValidator.validate_password(password)) == 0


class EmailValidator:
    """이메일 검증 클래스"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        이메일 형식 검증

        Args:
            email: 검증할 이메일

        Returns:
            bool: 유효한 이메일 형식 여부
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_email(email: str) -> str:
        """
        이메일 검증 및 정규화

        Args:
            email: 검증할 이메일

        Returns:
            str: 정규화된 이메일

        Raises:
            HTTPException: 이메일 형식이 잘못된 경우
        """
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이메일을 입력해주세요."
            )

        email = email.strip().lower()

        if not EmailValidator.is_valid_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="올바른 이메일 형식을 입력해주세요."
            )

        return email


class InputSanitizer:
    """입력 데이터 정제 클래스"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        문자열 입력 정제

        Args:
            value: 정제할 문자열
            max_length: 최대 길이

        Returns:
            str: 정제된 문자열
        """
        if not value:
            return ""

        # HTML 태그 제거
        value = re.sub(r'<[^>]+>', '', value)

        # 연속된 공백을 하나로 변환
        value = re.sub(r'\s+', ' ', value)

        # 앞뒤 공백 제거
        value = value.strip()

        # 최대 길이 제한
        if len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def sanitize_username(username: str) -> str:
        """
        사용자명 정제

        Args:
            username: 정제할 사용자명

        Returns:
            str: 정제된 사용자명

        Raises:
            HTTPException: 사용자명이 유효하지 않은 경우
        """
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자명을 입력해주세요."
            )

        username = username.strip()

        # 사용자명 형식 검증 (영문, 숫자, 언더스코어, 하이픈만 허용)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자명은 영문, 숫자, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다."
            )

        # 길이 제한 (3-20자)
        if len(username) < 3 or len(username) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자명은 3자 이상 20자 이하로 입력해주세요."
            )

        return username


class SecurityValidator:
    """보안 관련 검증 클래스"""

    @staticmethod
    def validate_session_code(session_code: str) -> str:
        """
        세션 코드 검증

        Args:
            session_code: 검증할 세션 코드

        Returns:
            str: 정제된 세션 코드

        Raises:
            HTTPException: 세션 코드가 유효하지 않은 경우
        """
        if not session_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="세션 코드를 입력해주세요."
            )

        session_code = session_code.strip().upper()

        # 세션 코드 형식 검증 (6자리 영숫자)
        if not re.match(r'^[A-Z0-9]{6}$', session_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="세션 코드는 6자리 영숫자여야 합니다."
            )

        return session_code

    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str] = None) -> bool:
        """
        리다이렉트 URL 안전성 검증

        Args:
            url: 검증할 URL
            allowed_hosts: 허용된 호스트 목록

        Returns:
            bool: 안전한 URL 여부
        """
        if not url:
            return False

        # 상대 경로면 안전
        if url.startswith('/') and not url.startswith('//'):
            return True

        # 허용된 호스트 목록이 있으면 검증
        if allowed_hosts:
            for host in allowed_hosts:
                if url.startswith(f'https://{host}') or url.startswith(f'http://{host}'):
                    return True

        return False