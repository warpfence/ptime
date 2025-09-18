# Backend 설정 템플릿

## 1. Docker 환경 설정

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=engagenow
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 2. FastAPI 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 앱 진입점
│   ├── config.py        # 설정 관리
│   ├── database.py      # DB 연결 설정
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마
│   ├── api/             # API 라우터
│   ├── core/            # 인증, 보안 등 핵심 기능
│   ├── services/        # 비즈니스 로직
│   ├── websocket/       # WebSocket 관련
│   └── utils/           # 유틸리티 함수
├── alembic/             # 데이터베이스 마이그레이션
├── tests/               # 테스트 파일
└── requirements.txt
```

## 3. requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
python-socketio==5.10.0
authlib==1.2.1
python-dotenv==1.0.0
loguru==0.7.2
slowapi==0.1.9
```

## 4. 기본 FastAPI 앱 구조

### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .api import auth, sessions
from .websocket.server import sio
from .core.logging import setup_logging

# 로깅 설정
setup_logging()

# FastAPI 앱 생성
app = FastAPI(title="EngageNow API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])

# 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Socket.io ASGI 앱으로 래핑
socket_app = socketio.ASGIApp(sio, app)
app = socket_app
```

### app/config.py
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str = "postgresql://postgres:password@localhost:5432/engagenow"
    redis_url: str = "redis://localhost:6379"

    # 인증 설정
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OAuth 설정
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # 기타 설정
    debug: bool = False
    cors_origins: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### app/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```