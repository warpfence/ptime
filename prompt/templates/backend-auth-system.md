# 백엔드 인증 시스템 구현 가이드

## 1. JWT 토큰 관리 시스템

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
```

## 2. Google OAuth 인증 시스템

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

class OAuthSessionManager:
    """OAuth 세션 관리 클래스"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, state: str, code_verifier: str, redirect_url: Optional[str] = None) -> None:
        """OAuth 세션 생성"""
        self._sessions[state] = {
            "code_verifier": code_verifier,
            "redirect_url": redirect_url,
            "created_at": secrets.token_hex(16)
        }

    def get_session(self, state: str) -> Optional[Dict[str, Any]]:
        """OAuth 세션 조회"""
        return self._sessions.get(state)

    def remove_session(self, state: str) -> None:
        """OAuth 세션 제거"""
        self._sessions.pop(state, None)

# 전역 인스턴스
google_oauth = GoogleOAuth()
oauth_session_manager = OAuthSessionManager()
```

## 3. 인증 미들웨어 및 의존성 주입

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
```

## 4. 입력 검증 및 보안 유틸리티

### app/core/validators.py

```python
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

        return errors

    @staticmethod
    def is_strong_password(password: str) -> bool:
        """패스워드 강도 확인"""
        return len(PasswordValidator.validate_password(password)) == 0

class EmailValidator:
    """이메일 검증 클래스"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_email(email: str) -> str:
        """이메일 검증 및 정규화"""
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
```

## 5. 인증 API 엔드포인트

### app/api/auth.py

```python
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    UserLogin, UserRegister, TokenResponse, PasswordChange,
    UserProfile, UserProfileUpdate
)
from ..core.security import JWTToken, PasswordHandler
from ..core.dependencies import get_current_active_user, verify_refresh_token
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

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: dict = Depends(verify_refresh_token),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """토큰 갱신"""
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
    """현재 사용자 정보 조회"""
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
    """패스워드 변경"""
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
```

## 6. OAuth API 엔드포인트

### app/api/oauth.py

```python
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.oauth import OAuthLoginResponse
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
    """Google OAuth 로그인 시작"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth 서비스를 사용할 수 없습니다."
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
    """Google OAuth 콜백 처리"""
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
            detail="유효하지 않은 OAuth 세션입니다."
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
    """OAuth 사용자 정보로 기존 사용자 조회하거나 새 사용자 생성"""
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
        existing_user.is_verified = True
        existing_user.last_login_at = datetime.utcnow()

        # 프로필 이미지가 없으면 Google 프로필 이미지 사용
        if not existing_user.profile_image and google_user_info.get("picture"):
            existing_user.profile_image = google_user_info["picture"]

        db.commit()
        db.refresh(existing_user)
        return existing_user

    # 새 사용자 생성
    random_password = PasswordHandler.hash_password("oauth_user_no_password")

    new_user = User(
        email=email,
        name=google_user_info.get("name", ""),
        username=None,
        hashed_password=random_password,
        google_id=google_user_info.get("id"),
        profile_image=google_user_info.get("picture"),
        is_active=True,
        is_verified=True,
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
    """Google 계정 연동 해제"""
    if not current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 계정이 연동되어 있지 않습니다."
        )

    # Google 연동 정보 제거
    current_user.google_id = None
    current_user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Google 계정 연동이 해제되었습니다."}
```

## 7. 데이터 스키마 정의

### app/schemas/auth.py

```python
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from ..core.validators import PasswordValidator, InputSanitizer

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

    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

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
```

## 8. 사용자 모델 정의

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

    # Relationships
    sessions = relationship("Session", back_populates="presenter")
```

## 9. 설정 파일

### app/config.py

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str = "postgresql://user:pass@localhost/db"

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

    # CORS 보안 설정
    allow_credentials: bool = True
    allowed_methods: list = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    allowed_headers: list = ["*"]

    # OAuth 설정
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"

    # OAuth 보안 설정
    oauth_state_secret: str = "oauth-state-secret-key"

    class Config:
        env_file = ".env"

settings = Settings()
```

## 10. 마이그레이션 및 배포

### 마이그레이션 설정

```bash
# Alembic 초기화
alembic init alembic

# 새 마이그레이션 생성
alembic revision --autogenerate -m "Add OAuth fields to User model"

# 마이그레이션 적용
alembic upgrade head
```

### 환경 변수 (.env)

```env
# 데이터베이스 설정
DATABASE_URL=postgresql://user:pass@localhost:5432/engagenow

# 인증 설정 (프로덕션에서는 강력한 SECRET_KEY 사용)
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 보안 설정
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
PASSWORD_MIN_LENGTH=8
REQUIRE_EMAIL_VERIFICATION=true

# Google OAuth 설정 (실제 값으로 교체)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback/google
OAUTH_STATE_SECRET=oauth-state-secret-key

# 기타 설정
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

### 필수 패키지 (requirements.txt)

```txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic-settings==2.10.1
passlib[bcrypt]==1.7.4
pyjwt==2.8.0
email-validator==2.1.0
httpx==0.27.0
python-multipart==0.0.6
python-dotenv==1.0.0
```