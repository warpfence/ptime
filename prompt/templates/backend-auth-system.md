# 인증 시스템

## 1. JWT 토큰 관리

### app/core/auth.py

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """리프레시 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> Dict[str, Any]:
    """액세스 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        raise JWTError("Token validation failed")

def verify_refresh_token(token: str) -> Dict[str, Any]:
    """리프레시 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        raise JWTError("Token validation failed")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해시화"""
    return pwd_context.hash(password)
```

## 2. Google OAuth 인증

### app/core/oauth.py

```python
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

class GoogleOAuth:
    """Google OAuth 클라이언트"""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

    def get_authorization_url(self, state: str = None) -> str:
        """Google OAuth 인증 URL 생성"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """인증 코드를 토큰으로 교환"""
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )

        return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """액세스 토큰으로 사용자 정보 조회"""
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )

        return response.json()

oauth_client = GoogleOAuth()
```

## 3. 인증 서비스

### app/services/auth_service.py

```python
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.auth import create_access_token, create_refresh_token
from app.core.oauth import oauth_client
from app.exceptions import AuthenticationException, ValidationException

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """ID로 사용자 조회"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Google ID로 사용자 조회"""
        return self.db.query(User).filter(User.google_id == google_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        """새 사용자 생성"""
        # 이메일 중복 확인
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValidationException("Email already registered")

        user = User(
            email=user_data.email,
            name=user_data.name,
            avatar_url=user_data.avatar_url,
            google_id=user_data.google_id,
            is_verified=True if user_data.google_id else False
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user: User) -> User:
        """마지막 로그인 시간 업데이트"""
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    async def authenticate_with_google(self, code: str) -> Dict[str, Any]:
        """Google OAuth로 인증"""
        try:
            # 인증 코드를 토큰으로 교환
            token_data = await oauth_client.exchange_code_for_token(code)
            access_token = token_data.get("access_token")

            if not access_token:
                raise AuthenticationException("Failed to get access token")

            # 사용자 정보 조회
            user_info = await oauth_client.get_user_info(access_token)

            # 사용자 찾기 또는 생성
            user = self.get_user_by_google_id(user_info["id"])

            if not user:
                # 이메일로 기존 사용자 확인
                user = self.get_user_by_email(user_info["email"])
                if user:
                    # 기존 사용자에 Google ID 연결
                    user.google_id = user_info["id"]
                    user.is_verified = True
                else:
                    # 새 사용자 생성
                    user_data = UserCreate(
                        email=user_info["email"],
                        name=user_info["name"],
                        avatar_url=user_info.get("picture"),
                        google_id=user_info["id"]
                    )
                    user = self.create_user(user_data)

            # 마지막 로그인 시간 업데이트
            user = self.update_last_login(user)

            # JWT 토큰 생성
            token_data = {
                "sub": str(user.id),
                "email": user.email,
            }

            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": UserResponse.from_orm(user)
            }

        except Exception as e:
            raise AuthenticationException(f"Google authentication failed: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """리프레시 토큰으로 새 액세스 토큰 발급"""
        from app.core.auth import verify_refresh_token

        try:
            payload = verify_refresh_token(refresh_token)
            user_id = payload.get("sub")

            user = self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationException("User not found or inactive")

            token_data = {
                "sub": str(user.id),
                "email": user.email,
            }

            new_access_token = create_access_token(token_data)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "user": UserResponse.from_orm(user)
            }

        except Exception as e:
            raise AuthenticationException("Invalid refresh token")
```

## 4. 인증 API 엔드포인트

### app/api/v1/auth.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.oauth import oauth_client

router = APIRouter()

@router.get("/login/google")
async def google_login(request: Request):
    """Google OAuth 로그인 시작"""
    # 상태 매개변수 생성 (CSRF 보호)
    state = "some_random_state"  # 실제로는 안전한 랜덤 문자열 생성
    authorization_url = oauth_client.get_authorization_url(state=state)

    return {"authorization_url": authorization_url}

@router.get("/callback/google")
async def google_callback(
    code: str,
    state: str = None,
    db: Session = Depends(get_db)
):
    """Google OAuth 콜백 처리"""
    auth_service = AuthService(db)

    try:
        result = await auth_service.authenticate_with_google(code)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """리프레시 토큰으로 새 액세스 토큰 발급"""
    auth_service = AuthService(db)

    try:
        result = auth_service.refresh_access_token(refresh_token)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """현재 로그인한 사용자 정보 조회"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return {"message": "Successfully logged out"}
```