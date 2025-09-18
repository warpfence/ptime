# 인증 시스템 템플릿

## 1. JWT 보안 설정

### app/core/security.py
```python
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
        """액세스 토큰 생성"""
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

        return jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """리프레시 토큰 생성 (7일 만료)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        return jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """JWT 토큰 디코드 및 검증"""
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

class PasswordHandler:
    """패스워드 해싱 및 검증 클래스"""

    @staticmethod
    def hash_password(password: str) -> str:
        """패스워드 해싱"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        return pwd_context.verify(plain_password, hashed_password)
```

## 2. 의존성 주입 시스템

### app/core/dependencies.py
```python
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
    """JWT 토큰에서 현재 사용자 정보를 가져오는 의존성 함수"""
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
    """현재 활성화된 사용자를 가져오는 의존성 함수"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다."
        )
    return current_user
```

## 3. Google OAuth 설정

### app/core/oauth.py
```python
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
        """OAuth state 파라미터 생성 (CSRF 보호)"""
        return secrets.token_urlsafe(32)

    def generate_pkce_challenge(self) -> tuple[str, str]:
        """PKCE (Proof Key for Code Exchange) 챌린지 생성"""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """Google OAuth 인증 URL 생성"""
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
        """인증 코드를 액세스 토큰으로 교환"""
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

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Google 사용자 정보 조회"""
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

google_oauth = GoogleOAuth()
```

## 4. 인증 API 라우터

### app/api/auth.py
```python
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.auth import UserLogin, UserRegister, TokenResponse, PasswordChange
from ..core.security import JWTToken, PasswordHandler
from ..core.dependencies import get_current_active_user
from ..config import settings

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """사용자 회원가입"""
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다."
        )

    # 새 사용자 생성
    hashed_password = PasswordHandler.hash_password(user_data.password)

    db_user = User(
        email=user_data.email,
        username=user_data.username,
        name=user_data.name,
        hashed_password=hashed_password,
        is_verified=not settings.require_email_verification
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
    """사용자 로그인"""
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
```

## 5. OAuth API 라우터

### app/api/oauth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.oauth import OAuthLoginResponse
from ..schemas.auth import TokenResponse
from ..core.oauth import google_oauth, oauth_session_manager
from ..core.security import JWTToken, PasswordHandler
from ..config import settings

router = APIRouter(prefix="/auth", tags=["OAuth 인증"])

@router.get("/login/google", response_model=OAuthLoginResponse)
async def google_login_start(
    redirect_url: str = Query(None, description="로그인 완료 후 리다이렉트할 URL")
) -> OAuthLoginResponse:
    """Google OAuth 로그인 시작"""
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
    db: Session = Depends(get_db)
):
    """Google OAuth 콜백 처리"""
    # 세션에서 OAuth 정보 조회
    session_data = oauth_session_manager.get_session(state)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 OAuth 세션입니다."
        )

    code_verifier = session_data["code_verifier"]

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

    return TokenResponse(
        access_token=our_access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )
```

## 6. 인증 스키마

### app/schemas/auth.py
```python
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from ..core.validators import PasswordValidator

class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    """사용자 회원가입 스키마"""
    email: EmailStr
    password: str
    password_confirm: str
    name: str
    username: Optional[str] = None

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
```

## 7. 보안 설정

### app/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 인증 설정
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 보안 설정
    max_login_attempts: int = 5
    account_lockout_minutes: int = 30
    password_min_length: int = 8
    require_email_verification: bool = True

    # OAuth 설정
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"

    class Config:
        env_file = ".env"

settings = Settings()
```

## 8. 사용자 모델

### app/models/user.py
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # OAuth 사용자는 NULL 가능

    # OAuth 관련 필드
    google_id = Column(String(255), unique=True, nullable=True)
    profile_image = Column(String(500), nullable=True)
    created_via_oauth = Column(Boolean, default=False)

    # 계정 상태
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # 타임스탬프
    last_login_at = Column(DateTime, nullable=True)
```