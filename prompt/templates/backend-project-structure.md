# Backend 프로젝트 구조 표준화

## 1. FastAPI 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 설정
│   ├── database.py             # 데이터베이스 연결
│   ├── dependencies.py         # 의존성 주입
│   ├── exceptions.py           # 커스텀 예외
│   ├── models/                 # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── participant.py
│   │   └── message.py
│   ├── schemas/                # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── participant.py
│   │   └── message.py
│   ├── api/                    # API 라우터
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── sessions.py
│   │   │   ├── participants.py
│   │   │   └── messages.py
│   │   └── deps.py
│   ├── core/                   # 핵심 기능
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── security.py
│   │   ├── config.py
│   │   └── events.py
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── session_service.py
│   │   ├── participant_service.py
│   │   └── websocket_service.py
│   ├── utils/                  # 유틸리티 함수
│   │   ├── __init__.py
│   │   ├── qr_generator.py
│   │   ├── validators.py
│   │   └── helpers.py
│   └── websocket/              # WebSocket 관련
│       ├── __init__.py
│       ├── manager.py
│       ├── handlers.py
│       └── events.py
├── tests/                      # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_sessions.py
│   └── test_websocket.py
├── alembic/                    # 데이터베이스 마이그레이션
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## 2. 개발 표준 및 컨벤션

### 파일 명명 규칙
- **모델 파일**: snake_case (예: `user.py`, `session_participant.py`)
- **스키마 파일**: 모델과 동일한 이름 (예: `user.py`)
- **라우터 파일**: 복수형 사용 (예: `sessions.py`, `participants.py`)
- **서비스 파일**: `{domain}_service.py` 형태

### Import 순서 규칙
```python
# 1. 표준 라이브러리
import os
from datetime import datetime
from typing import List, Optional

# 2. 외부 라이브러리
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. 프로젝트 내부 모듈
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
```

### 코드 스타일 가이드
- **함수명**: snake_case
- **클래스명**: PascalCase
- **상수명**: UPPER_SNAKE_CASE
- **변수명**: snake_case
- **타입 힌트**: 모든 함수와 메서드에 필수
- **Docstring**: Google 스타일 사용