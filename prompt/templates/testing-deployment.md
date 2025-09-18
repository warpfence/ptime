# 테스팅 및 배포 템플릿

## 1. 단위 테스트

### Backend 테스트 설정
#### tests/conftest.py
```python
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base
from app.core.security import create_access_token
from app.models.user import User

# 테스트 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="test123"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### 세션 API 테스트
#### tests/test_sessions.py
```python
import pytest
from fastapi.testclient import TestClient

def test_create_session(client: TestClient, auth_headers):
    """세션 생성 테스트"""
    session_data = {
        "title": "테스트 세션",
        "description": "테스트용 세션입니다."
    }

    response = client.post("/api/sessions", json=session_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == session_data["title"]
    assert data["description"] == session_data["description"]
    assert "session_code" in data
    assert len(data["session_code"]) == 6
    assert "qr_code_url" in data

def test_get_sessions(client: TestClient, auth_headers):
    """세션 목록 조회 테스트"""
    # 세션 생성
    session_data = {"title": "테스트 세션"}
    client.post("/api/sessions", json=session_data, headers=auth_headers)

    # 목록 조회
    response = client.get("/api/sessions", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == session_data["title"]

def test_session_code_uniqueness(client: TestClient, auth_headers):
    """세션 코드 고유성 테스트"""
    codes = set()

    for i in range(10):
        session_data = {"title": f"테스트 세션 {i}"}
        response = client.post("/api/sessions", json=session_data, headers=auth_headers)
        data = response.json()
        codes.add(data["session_code"])

    # 모든 세션 코드가 고유해야 함
    assert len(codes) == 10

def test_unauthorized_access(client: TestClient):
    """인증되지 않은 접근 테스트"""
    response = client.get("/api/sessions")
    assert response.status_code == 401

def test_join_session(client: TestClient, auth_headers):
    """세션 참여 테스트"""
    # 세션 생성
    session_data = {"title": "참여 테스트 세션"}
    create_response = client.post("/api/sessions", json=session_data, headers=auth_headers)
    session_code = create_response.json()["session_code"]

    # 세션 활성화
    client.post(f"/api/sessions/{create_response.json()['id']}/activate", headers=auth_headers)

    # 세션 참여
    join_data = {"nickname": "테스트참여자"}
    response = client.post(f"/api/join/{session_code}", json=join_data)

    assert response.status_code == 200
    data = response.json()
    assert data["participant"]["nickname"] == join_data["nickname"]
    assert data["session"]["session_code"] == session_code

def test_duplicate_nickname(client: TestClient, auth_headers):
    """닉네임 중복 테스트"""
    # 세션 생성 및 활성화
    session_data = {"title": "중복 테스트 세션"}
    create_response = client.post("/api/sessions", json=session_data, headers=auth_headers)
    session_code = create_response.json()["session_code"]
    client.post(f"/api/sessions/{create_response.json()['id']}/activate", headers=auth_headers)

    # 첫 번째 참여자
    join_data = {"nickname": "중복닉네임"}
    response1 = client.post(f"/api/join/{session_code}", json=join_data)
    assert response1.status_code == 200

    # 동일 닉네임으로 두 번째 참여 시도
    response2 = client.post(f"/api/join/{session_code}", json=join_data)
    assert response2.status_code == 400
    assert "이미 사용중인 닉네임" in response2.json()["detail"]
```

### WebSocket 테스트
#### tests/test_websocket.py
```python
import pytest
import asyncio
from socketio import AsyncClient

@pytest.mark.asyncio
async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    sio = AsyncClient()

    try:
        await sio.connect('http://localhost:8000')
        assert sio.connected

        # 연결 확인 이벤트 수신
        received_events = []

        @sio.event
        async def connected(data):
            received_events.append(('connected', data))

        await asyncio.sleep(1)  # 이벤트 수신 대기
        assert len(received_events) > 0

    finally:
        await sio.disconnect()

@pytest.mark.asyncio
async def test_join_session_websocket():
    """WebSocket 세션 참여 테스트"""
    sio = AsyncClient()

    try:
        await sio.connect('http://localhost:8000')

        # 세션 참여
        await sio.emit('join_session', {
            'session_id': 'test-session-id',
            'participant_id': 'test-participant-id',
            'nickname': 'TestUser'
        })

        # 응답 대기
        response = await sio.receive()
        assert response[0] == 'joined_session'

    finally:
        await sio.disconnect()
```

## 2. E2E 테스트

### Playwright 설정
#### playwright.config.ts
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2E 테스트 시나리오
#### tests/e2e/session-flow.spec.ts
```typescript
import { test, expect } from '@playwright/test'

test.describe('세션 전체 플로우', () => {
  test('발표자가 세션을 생성하고 참여자가 채팅 참여', async ({ browser }) => {
    // 발표자 브라우저 컨텍스트
    const presenterContext = await browser.newContext()
    const presenterPage = await presenterContext.newPage()

    // 참여자 브라우저 컨텍스트
    const participantContext = await browser.newContext()
    const participantPage = await participantContext.newPage()

    try {
      // 1. 발표자 로그인 (테스트용 로그인)
      await presenterPage.goto('/auth/test-login')
      await presenterPage.fill('[data-testid="test-email"]', 'presenter@test.com')
      await presenterPage.click('[data-testid="test-login-button"]')

      // 2. 대시보드로 이동
      await presenterPage.goto('/dashboard')
      await expect(presenterPage.locator('h1')).toContainText('내 세션')

      // 3. 세션 생성
      await presenterPage.click('[data-testid="create-session-button"]')
      await presenterPage.fill('[data-testid="session-title"]', 'E2E 테스트 세션')
      await presenterPage.fill('[data-testid="session-description"]', '자동화 테스트용 세션')
      await presenterPage.click('[data-testid="create-button"]')

      // 4. 세션 코드 확인
      const sessionCodeElement = presenterPage.locator('[data-testid="session-code"]')
      await expect(sessionCodeElement).toBeVisible()
      const sessionCode = await sessionCodeElement.textContent()

      // 5. 세션 활성화
      await presenterPage.click('[data-testid="activate-session"]')
      await expect(presenterPage.locator('[data-testid="session-status"]')).toContainText('진행중')

      // 6. 채팅 기능 활성화
      await presenterPage.click('[data-testid="activate-chat"]')

      // 7. 참여자가 세션 참여
      await participantPage.goto(`/join/${sessionCode}`)
      await participantPage.fill('[data-testid="nickname-input"]', 'E2E테스터')
      await participantPage.click('[data-testid="join-button"]')

      // 8. 참여자 페이지 로드 확인
      await expect(participantPage.locator('[data-testid="chat-container"]')).toBeVisible()

      // 9. 발표자가 참여자 수 확인
      await expect(presenterPage.locator('[data-testid="participant-count"]')).toContainText('1명')

      // 10. 참여자가 메시지 전송
      await participantPage.fill('[data-testid="chat-input"]', '안녕하세요! E2E 테스트입니다.')
      await participantPage.click('[data-testid="send-button"]')

      // 11. 발표자가 메시지 수신 확인
      await expect(presenterPage.locator('[data-testid="chat-messages"]'))
        .toContainText('안녕하세요! E2E 테스트입니다.')

      // 12. 발표자가 응답 메시지 전송
      await presenterPage.fill('[data-testid="chat-input"]', '네, 반갑습니다!')
      await presenterPage.click('[data-testid="send-button"]')

      // 13. 참여자가 응답 메시지 수신 확인
      await expect(participantPage.locator('[data-testid="chat-messages"]'))
        .toContainText('네, 반갑습니다!')

      // 14. 이모지 반응 테스트
      await participantPage.click('[data-testid="emoji-👍"]')
      await expect(presenterPage.locator('[data-testid="chat-messages"]')).toContainText('👍')

    } finally {
      await presenterContext.close()
      await participantContext.close()
    }
  })

  test('모바일 환경에서 세션 참여', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 12']
    })
    const page = await context.newPage()

    try {
      // QR 코드로 세션 참여 (테스트용 세션 코드 사용)
      await page.goto('/join/TEST123')

      // 모바일 최적화 확인
      const nicknameInput = page.locator('[data-testid="nickname-input"]')
      await expect(nicknameInput).toBeVisible()

      // 닉네임 입력
      await nicknameInput.fill('모바일사용자')
      await page.click('[data-testid="join-button"]')

      // 채팅 UI 모바일 최적화 확인
      await expect(page.locator('[data-testid="chat-container"]')).toBeVisible()

      // 터치 입력 테스트
      await page.tap('[data-testid="emoji-😀"]')
      await page.fill('[data-testid="chat-input"]', '모바일에서 테스트 중입니다!')
      await page.tap('[data-testid="send-button"]')

    } finally {
      await context.close()
    }
  })
})
```

## 3. 성능 테스트

### 부하 테스트 (Locust)
#### tests/load/locustfile.py
```python
from locust import HttpUser, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
import string
import json

class EngageNowUser(FastHttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """사용자 시작 시 실행"""
        # 테스트용 토큰 획득
        response = self.client.post("/auth/test-login", json={
            "email": f"test_{self.generate_random_string(8)}@example.com",
            "name": f"Test User {random.randint(1, 10000)}"
        })

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def generate_random_string(self, length):
        return ''.join(random.choices(string.ascii_letters, k=length))

    @task(3)
    def create_session(self):
        """세션 생성 테스트"""
        if not self.token:
            return

        session_data = {
            "title": f"부하테스트 세션 {random.randint(1, 1000)}",
            "description": "Locust 부하 테스트용 세션"
        }

        with self.client.post("/api/sessions",
                            json=session_data,
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Session creation failed: {response.status_code}")

    @task(5)
    def get_sessions(self):
        """세션 목록 조회 테스트"""
        if not self.token:
            return

        with self.client.get("/api/sessions",
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get sessions failed: {response.status_code}")

    @task(2)
    def join_session_as_participant(self):
        """참여자로 세션 참여 테스트"""
        # 미리 생성된 활성 세션에 참여
        session_codes = ["TEST01", "TEST02", "TEST03"]  # 테스트용 세션 코드들
        session_code = random.choice(session_codes)

        participant_data = {
            "nickname": f"참여자{random.randint(1, 10000)}"
        }

        with self.client.post(f"/api/join/{session_code}",
                            json=participant_data,
                            catch_response=True) as response:
            if response.status_code in [200, 400]:  # 400은 중복 닉네임 등 정상적인 오류
                response.success()
            else:
                response.failure(f"Join session failed: {response.status_code}")

class WebSocketUser(HttpUser):
    """WebSocket 연결 부하 테스트"""
    wait_time = between(2, 5)

    def on_start(self):
        # WebSocket 연결 시뮬레이션을 위한 HTTP 엔드포인트 호출
        pass

    @task
    def simulate_websocket_activity(self):
        """WebSocket 활동 시뮬레이션"""
        # 실제 구현에서는 WebSocket 라이브러리를 사용해야 함
        # 여기서는 HTTP로 WebSocket 활동을 시뮬레이션
        session_id = f"session_{random.randint(1, 100)}"

        # 연결 시뮬레이션
        self.client.get(f"/health")  # 단순한 헬스체크로 서버 부하 생성
```

### WebSocket 동시 연결 테스트
#### tests/load/websocket_load.py
```python
import asyncio
import socketio
import time
import random
from concurrent.futures import ThreadPoolExecutor

class WebSocketLoadTester:
    def __init__(self, server_url, max_connections=1000):
        self.server_url = server_url
        self.max_connections = max_connections
        self.connected_clients = []
        self.message_count = 0
        self.start_time = None

    async def create_client(self, client_id):
        """단일 클라이언트 생성 및 연결"""
        try:
            sio = socketio.AsyncClient()

            @sio.event
            async def connect():
                print(f"Client {client_id} connected")

                # 세션 참여
                await sio.emit('join_session', {
                    'session_id': 'load-test-session',
                    'participant_id': f'participant-{client_id}',
                    'nickname': f'LoadTester{client_id}'
                })

            @sio.event
            async def new_message(data):
                self.message_count += 1

            await sio.connect(self.server_url)
            self.connected_clients.append(sio)

            # 랜덤한 간격으로 메시지 전송
            while True:
                await asyncio.sleep(random.uniform(5, 15))
                await sio.emit('send_message', {
                    'message': f'Load test message from client {client_id}',
                    'message_type': 'text'
                })

        except Exception as e:
            print(f"Client {client_id} error: {e}")

    async def run_load_test(self, duration_seconds=300):
        """부하 테스트 실행"""
        self.start_time = time.time()

        # 동시 연결 생성
        tasks = []
        for i in range(self.max_connections):
            task = asyncio.create_task(self.create_client(i))
            tasks.append(task)

            # 연결 간격 조절 (서버 과부하 방지)
            if i % 50 == 0:
                await asyncio.sleep(1)

        print(f"Started {self.max_connections} concurrent connections")

        # 지정된 시간 동안 테스트 실행
        await asyncio.sleep(duration_seconds)

        # 통계 출력
        elapsed_time = time.time() - self.start_time
        print(f"Test completed after {elapsed_time:.2f} seconds")
        print(f"Connected clients: {len(self.connected_clients)}")
        print(f"Total messages processed: {self.message_count}")
        print(f"Messages per second: {self.message_count / elapsed_time:.2f}")

        # 연결 정리
        for client in self.connected_clients:
            await client.disconnect()

# 실행 스크립트
async def main():
    tester = WebSocketLoadTester('http://localhost:8000', max_connections=500)
    await tester.run_load_test(duration_seconds=180)  # 3분간 테스트

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. 배포 설정

### 프로덕션 Docker Compose
#### docker-compose.prod.yml
```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.engagenow.com
      - NEXT_PUBLIC_WEBSOCKET_URL=https://api.engagenow.com
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### CI/CD GitHub Actions
#### .github/workflows/deploy.yml
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install Python dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio

    - name: Install Node.js dependencies
      run: |
        cd frontend
        npm ci

    - name: Run Python tests
      run: |
        cd backend
        pytest tests/ -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379

    - name: Run Frontend tests
      run: |
        cd frontend
        npm run test

    - name: Build Frontend
      run: |
        cd frontend
        npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.7
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/engagenow
          git pull origin main
          docker-compose -f docker-compose.prod.yml down
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml up -d

          # 헬스체크
          sleep 30
          curl -f http://localhost:8000/health || exit 1
```