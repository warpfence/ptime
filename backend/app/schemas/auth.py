"""
인증 관련 Pydantic 스키마들
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from ..core.validators import PasswordValidator, InputSanitizer


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 토큰 만료 시간 (초)


class TokenRefresh(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str


class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    email: EmailStr
    password: str

    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('패스워드를 입력해주세요.')
        return v


class UserRegister(BaseModel):
    """사용자 회원가입 스키마"""
    email: EmailStr
    password: str
    password_confirm: str
    name: str
    username: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

    @validator('name')
    def validate_name(cls, v):
        if not v:
            raise ValueError('이름을 입력해주세요.')
        return InputSanitizer.sanitize_string(v, 50)

    @validator('username')
    def validate_username(cls, v):
        if v:
            return InputSanitizer.sanitize_username(v)
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        errors = PasswordValidator.validate_password(v)
        if errors:
            raise ValueError(' '.join(errors))
        return v

    @validator('password_confirm')
    def validate_passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('패스워드가 일치하지 않습니다.')
        return v


class PasswordChange(BaseModel):
    """패스워드 변경 스키마"""
    current_password: str
    new_password: str
    new_password_confirm: str

    @validator('new_password')
    def validate_new_password_strength(cls, v):
        errors = PasswordValidator.validate_password(v)
        if errors:
            raise ValueError(' '.join(errors))
        return v

    @validator('new_password_confirm')
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 패스워드가 일치하지 않습니다.')
        return v


class PasswordReset(BaseModel):
    """패스워드 재설정 요청 스키마"""
    email: EmailStr

    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """패스워드 재설정 확인 스키마"""
    token: str
    new_password: str
    new_password_confirm: str

    @validator('new_password')
    def validate_new_password_strength(cls, v):
        errors = PasswordValidator.validate_password(v)
        if errors:
            raise ValueError(' '.join(errors))
        return v

    @validator('new_password_confirm')
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('패스워드가 일치하지 않습니다.')
        return v


class EmailVerification(BaseModel):
    """이메일 인증 스키마"""
    token: str


class UserProfile(BaseModel):
    """사용자 프로필 응답 스키마"""
    id: int
    email: str
    username: Optional[str]
    name: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """사용자 프로필 수정 스키마"""
    name: Optional[str] = None
    username: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('이름을 입력해주세요.')
            return InputSanitizer.sanitize_string(v, 50)
        return v

    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if v.strip():
                return InputSanitizer.sanitize_username(v)
            else:
                return None  # 빈 문자열을 None으로 변환
        return v


class LoginAttempt(BaseModel):
    """로그인 시도 기록 스키마"""
    email: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    attempted_at: str

    class Config:
        from_attributes = True


class SecurityLog(BaseModel):
    """보안 로그 스키마"""
    user_id: Optional[int]
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[dict] = None
    created_at: str

    class Config:
        from_attributes = True