from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .api import auth, oauth, sessions, participants
from .services.websocket_manager import get_websocket_manager

# FastAPI 앱 생성
app = FastAPI(title="EngageNow API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WebSocket 연결을 위해 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(participants.router)

# WebSocket 매니저 초기화
websocket_manager = get_websocket_manager()

# 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# WebSocket 상태 확인 엔드포인트
@app.get("/api/websocket/status")
def websocket_status():
    return {
        "status": "active",
        "total_connections": websocket_manager.get_total_connections(),
        "active_sessions": len(websocket_manager.session_rooms)
    }

# Socket.io ASGI 앱으로 래핑
socket_app = socketio.ASGIApp(websocket_manager.sio, app)

# uvicorn이 사용할 최종 앱 (Socket.io 통합)
app = socket_app