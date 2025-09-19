from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .api import auth, oauth, sessions
# from .websocket.server import sio
# from .core.logging import setup_logging

# 로깅 설정
# setup_logging()

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
app.include_router(auth.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")

# 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Socket.io ASGI 앱으로 래핑 (추후 구현)
# socket_app = socketio.ASGIApp(sio, app)
# app = socket_app