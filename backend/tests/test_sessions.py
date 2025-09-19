"""
세션 CRUD API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.session import Session
from app.core.security import JWTToken
import uuid

# 테스트용 데이터베이스 설정 (메모리 내 SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테스트용 데이터베이스 종속성 오버라이드
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 테스트 클라이언트 생성
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """각 테스트 함수마다 깨끗한 데이터베이스 세션 제공"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """인증된 사용자의 헤더 생성"""
    access_token = JWTToken.create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_session(db_session, test_user):
    """테스트용 세션 생성"""
    session = Session(
        id=uuid.uuid4(),
        presenter_id=test_user.id,
        title="Test Session",
        description="Test Description",
        session_code="TEST01",
        qr_code_url="data:image/png;base64,test",
        is_active=False
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


class TestSessionAPI:
    """세션 API 테스트 클래스"""

    def test_create_session_success(self, auth_headers):
        """세션 생성 성공 테스트"""
        session_data = {
            "title": "새로운 세션",
            "description": "세션 설명"
        }

        response = client.post(
            "/api/sessions/",
            json=session_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == session_data["title"]
        assert data["description"] == session_data["description"]
        assert len(data["session_code"]) == 6
        assert data["qr_code_url"].startswith("data:image/png;base64,")
        assert data["is_active"] is False
        assert data["participant_count"] == 0

    def test_create_session_invalid_title(self, auth_headers):
        """세션 생성 실패 테스트 - 유효하지 않은 제목"""
        session_data = {
            "title": "a",  # 2자 미만
            "description": "세션 설명"
        }

        response = client.post(
            "/api/sessions/",
            json=session_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_session_unauthorized(self):
        """세션 생성 실패 테스트 - 인증 없음"""
        session_data = {
            "title": "새로운 세션",
            "description": "세션 설명"
        }

        response = client.post("/api/sessions/", json=session_data)
        assert response.status_code == 403

    def test_get_my_sessions(self, auth_headers, test_session):
        """내 세션 목록 조회 테스트"""
        response = client.get("/api/sessions/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_session.id)
        assert data[0]["title"] == test_session.title

    def test_get_session_by_id(self, auth_headers, test_session):
        """세션 상세 조회 테스트"""
        response = client.get(
            f"/api/sessions/{test_session.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_session.id)
        assert data["title"] == test_session.title
        assert data["qr_code_url"] is not None

    def test_get_session_not_found(self, auth_headers):
        """존재하지 않는 세션 조회 테스트"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/sessions/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_session(self, auth_headers, test_session):
        """세션 수정 테스트"""
        update_data = {
            "title": "수정된 제목",
            "description": "수정된 설명"
        }

        response = client.put(
            f"/api/sessions/{test_session.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    def test_delete_session(self, auth_headers, test_session):
        """세션 삭제 테스트"""
        response = client.delete(
            f"/api/sessions/{test_session.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # 삭제 확인
        response = client.get(
            f"/api/sessions/{test_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_activate_session(self, auth_headers, test_session):
        """세션 활성화 테스트"""
        response = client.post(
            f"/api/sessions/{test_session.id}/activate",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "세션이 활성화되었습니다."
        assert data["session"]["is_active"] is True

    def test_deactivate_session(self, auth_headers, test_session):
        """세션 비활성화 테스트"""
        # 먼저 활성화
        client.post(
            f"/api/sessions/{test_session.id}/activate",
            headers=auth_headers
        )

        # 비활성화
        response = client.post(
            f"/api/sessions/{test_session.id}/deactivate",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "세션이 비활성화되었습니다."
        assert data["session"]["is_active"] is False

    def test_get_session_by_code(self, test_session):
        """세션 코드로 조회 테스트 (인증 불필요)"""
        response = client.get(f"/api/sessions/code/{test_session.session_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_code"] == test_session.session_code
        assert data["title"] == test_session.title

    def test_get_session_by_invalid_code(self):
        """유효하지 않은 세션 코드 조회 테스트"""
        response = client.get("/api/sessions/code/INVALID")

        assert response.status_code == 404