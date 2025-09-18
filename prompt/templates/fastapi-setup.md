# FastAPI 설정 및 미들웨어

## 1. 기본 FastAPI 앱 설정

### app/main.py

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.api.v1 import auth, sessions, participants, messages
from app.database import engine
from app.models import Base
from app.exceptions import CustomException

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="EngageNow API - 실시간 청중 참여 플랫폼",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response

# 예외 핸들러
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )

# 라우터 등록
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["sessions"])
app.include_router(participants.router, prefix=f"{settings.API_V1_STR}/participants", tags=["participants"])
app.include_router(messages.router, prefix=f"{settings.API_V1_STR}/messages", tags=["messages"])

# 라이프사이클 이벤트
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up EngageNow API...")
    # 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down EngageNow API...")

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
```

## 2. 환경 설정

### app/core/config.py

```python
from pydantic import BaseSettings, validator
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "EngageNow API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # 보안 설정
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30일

    # 데이터베이스 설정
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    # CORS 설정
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # OAuth 설정
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Email 설정 (선택)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 3. 의존성 주입

### app/dependencies.py

```python
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import SessionLocal
from app.core.config import settings
from app.core.auth import verify_access_token
from app.models.user import User
from app.services.auth_service import AuthService

security = HTTPBearer()

def get_db() -> Generator:
    """데이터베이스 세션 의존성"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 인증된 사용자 반환"""
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 상태인 현재 사용자 반환"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
```

## 4. 커스텀 예외

### app/exceptions.py

```python
from fastapi import HTTPException

class CustomException(HTTPException):
    """커스텀 예외 기본 클래스"""
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class AuthenticationException(CustomException):
    """인증 관련 예외"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail, error_code="AUTH_ERROR")

class AuthorizationException(CustomException):
    """권한 관련 예외"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=403, detail=detail, error_code="PERMISSION_ERROR")

class NotFoundException(CustomException):
    """리소스를 찾을 수 없는 예외"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND")

class ValidationException(CustomException):
    """유효성 검사 예외"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=422, detail=detail, error_code="VALIDATION_ERROR")

class SessionException(CustomException):
    """세션 관련 예외"""
    def __init__(self, detail: str = "Session error", error_code: str = "SESSION_ERROR"):
        super().__init__(status_code=400, detail=detail, error_code=error_code)
```