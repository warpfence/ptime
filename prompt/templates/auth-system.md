# 인증 시스템 템플릿

## 1. JWT 보안 설정

### app/core/security.py
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..config import settings

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## 2. 의존성 주입

### app/core/deps.py
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .security import verify_token
from ..database import get_db
from ..models.user import User

security = HTTPBearer()

def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
    user_id = verify_token(token.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 3. Google OAuth 설정

### app/core/oauth.py
```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from ..config import settings

config = Config('.env')
oauth = OAuth()

google = oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
```

## 4. 인증 API 라우터

### app/api/auth.py
```python
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.oauth import google
from ..database import get_db
from ..models.user import User
from ..core.security import create_access_token
from ..schemas.auth import TokenResponse

router = APIRouter()

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await google.authorize_redirect(request, redirect_uri)

@router.get("/callback/google", response_model=TokenResponse)
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    token = await google.authorize_access_token(request)
    user_info = token.get('userinfo')

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    # 사용자 생성 또는 조회
    user = db.query(User).filter(User.email == user_info['email']).first()
    if not user:
        user = User(
            email=user_info['email'],
            name=user_info['name'],
            provider='google',
            provider_id=user_info['sub']
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": current_user}
```

## 5. 인증 스키마

### app/schemas/auth.py
```python
from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    provider: str

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

## 6. 보안 미들웨어

### app/middleware/security.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

def setup_security_middleware(app: FastAPI):
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 신뢰할 수 있는 호스트만 허용
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "your-domain.com"]
    )

    # Rate Limiting 설정
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate Limiting 데코레이터 사용 예시
# @limiter.limit("5/minute")
# def limited_endpoint(request: Request):
#     return {"message": "This endpoint is rate limited"}
```