# WebSocket 및 실시간 통신

## 1. WebSocket 연결 관리자

### app/websocket/manager.py

```python
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import uuid
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 세션별 연결 관리
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 참가자별 세션 매핑
        self.participant_sessions: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, session_code: str, participant_id: str):
        """새 WebSocket 연결 수락"""
        await websocket.accept()

        if session_code not in self.active_connections:
            self.active_connections[session_code] = {}

        self.active_connections[session_code][participant_id] = websocket
        self.participant_sessions[participant_id] = session_code

        logger.info(f"Participant {participant_id} connected to session {session_code}")

        # 다른 참가자들에게 새 참가자 알림
        await self.broadcast_to_session(session_code, {
            "type": "participant_joined",
            "participant_id": participant_id,
            "message": f"새 참가자가 접속했습니다."
        }, exclude_participant=participant_id)

    def disconnect(self, participant_id: str):
        """WebSocket 연결 해제"""
        session_code = self.participant_sessions.get(participant_id)
        if session_code and session_code in self.active_connections:
            if participant_id in self.active_connections[session_code]:
                del self.active_connections[session_code][participant_id]

            # 세션에 연결된 참가자가 없으면 세션 정리
            if not self.active_connections[session_code]:
                del self.active_connections[session_code]

        if participant_id in self.participant_sessions:
            del self.participant_sessions[participant_id]

        logger.info(f"Participant {participant_id} disconnected from session {session_code}")

    async def send_personal_message(self, message: dict, participant_id: str):
        """특정 참가자에게 메시지 전송"""
        session_code = self.participant_sessions.get(participant_id)
        if session_code and session_code in self.active_connections:
            websocket = self.active_connections[session_code].get(participant_id)
            if websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to {participant_id}: {e}")
                    self.disconnect(participant_id)

    async def broadcast_to_session(self, session_code: str, message: dict, exclude_participant: str = None):
        """세션의 모든 참가자에게 메시지 브로드캐스트"""
        if session_code not in self.active_connections:
            return

        disconnected_participants = []

        for participant_id, websocket in self.active_connections[session_code].items():
            if exclude_participant and participant_id == exclude_participant:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {participant_id}: {e}")
                disconnected_participants.append(participant_id)

        # 연결이 끊어진 참가자들 정리
        for participant_id in disconnected_participants:
            self.disconnect(participant_id)

    def get_session_participants(self, session_code: str) -> List[str]:
        """세션에 연결된 참가자 목록 반환"""
        if session_code in self.active_connections:
            return list(self.active_connections[session_code].keys())
        return []

    def get_participant_count(self, session_code: str) -> int:
        """세션 참가자 수 반환"""
        if session_code in self.active_connections:
            return len(self.active_connections[session_code])
        return 0

# 전역 연결 관리자 인스턴스
manager = ConnectionManager()
```

## 2. WebSocket 이벤트 핸들러

### app/websocket/handlers.py

```python
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import uuid

from app.websocket.manager import manager
from app.database import get_db
from app.services.message_service import MessageService
from app.services.participant_service import ParticipantService
from app.models.message import MessageType
from app.schemas.message import MessageCreate

class WebSocketHandler:
    """WebSocket 이벤트 처리"""

    def __init__(self, db: Session):
        self.db = db
        self.message_service = MessageService(db)
        self.participant_service = ParticipantService(db)

    async def handle_message(self, websocket: WebSocket, data: Dict[str, Any], participant_id: str):
        """수신된 메시지 처리"""
        message_type = data.get("type")

        handlers = {
            "chat_message": self._handle_chat_message,
            "question": self._handle_question,
            "participant_update": self._handle_participant_update,
            "typing": self._handle_typing_indicator,
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(websocket, data, participant_id)
        else:
            await self._send_error(websocket, f"Unknown message type: {message_type}")

    async def _handle_chat_message(self, websocket: WebSocket, data: Dict[str, Any], participant_id: str):
        """채팅 메시지 처리"""
        try:
            content = data.get("content", "").strip()
            if not content:
                await self._send_error(websocket, "Message content cannot be empty")
                return

            # 참가자 정보 조회
            participant = self.participant_service.get_participant_by_id(participant_id)
            if not participant:
                await self._send_error(websocket, "Participant not found")
                return

            # 메시지 데이터베이스에 저장
            message_data = MessageCreate(
                content=content,
                message_type=MessageType.CHAT,
                session_id=participant.session_id
            )
            message = self.message_service.send_message(message_data, participant_id)

            # 세션의 모든 참가자에게 브로드캐스트
            session = participant.session
            broadcast_data = {
                "type": "chat_message",
                "message_id": str(message.id),
                "content": message.content,
                "participant_id": participant_id,
                "participant_nickname": participant.nickname,
                "timestamp": message.created_at.isoformat(),
                "session_code": session.session_code
            }

            await manager.broadcast_to_session(session.session_code, broadcast_data)

        except Exception as e:
            await self._send_error(websocket, f"Failed to send message: {str(e)}")

    async def _handle_question(self, websocket: WebSocket, data: Dict[str, Any], participant_id: str):
        """질문 메시지 처리"""
        try:
            content = data.get("content", "").strip()
            if not content:
                await self._send_error(websocket, "Question content cannot be empty")
                return

            # 참가자 정보 조회
            participant = self.participant_service.get_participant_by_id(participant_id)
            if not participant:
                await self._send_error(websocket, "Participant not found")
                return

            # 질문을 데이터베이스에 저장
            message_data = MessageCreate(
                content=content,
                message_type=MessageType.QUESTION,
                session_id=participant.session_id
            )
            message = self.message_service.send_message(message_data, participant_id)

            # 호스트에게만 알림 (일반 참가자들에게는 선택적)
            session = participant.session
            question_data = {
                "type": "question",
                "message_id": str(message.id),
                "content": message.content,
                "participant_id": participant_id,
                "participant_nickname": participant.nickname,
                "timestamp": message.created_at.isoformat(),
                "session_code": session.session_code
            }

            # 모든 참가자에게 브로드캐스트 (호스트 설정에 따라 변경 가능)
            await manager.broadcast_to_session(session.session_code, question_data)

        except Exception as e:
            await self._send_error(websocket, f"Failed to send question: {str(e)}")

    async def _handle_participant_update(self, websocket: WebSocket, data: Dict[str, Any], participant_id: str):
        """참가자 정보 업데이트 처리"""
        try:
            # 참가자 온라인 상태 업데이트
            self.participant_service.update_participant_status(participant_id, is_online=True)

            participant = self.participant_service.get_participant_by_id(participant_id)
            if participant:
                session = participant.session
                update_data = {
                    "type": "participant_update",
                    "participant_id": participant_id,
                    "participant_nickname": participant.nickname,
                    "is_online": participant.is_online,
                    "session_code": session.session_code
                }

                await manager.broadcast_to_session(session.session_code, update_data)

        except Exception as e:
            await self._send_error(websocket, f"Failed to update participant: {str(e)}")

    async def _handle_typing_indicator(self, websocket: WebSocket, data: Dict[str, Any], participant_id: str):
        """타이핑 인디케이터 처리"""
        try:
            is_typing = data.get("is_typing", False)

            participant = self.participant_service.get_participant_by_id(participant_id)
            if participant:
                session = participant.session
                typing_data = {
                    "type": "typing",
                    "participant_id": participant_id,
                    "participant_nickname": participant.nickname,
                    "is_typing": is_typing,
                    "session_code": session.session_code
                }

                await manager.broadcast_to_session(
                    session.session_code,
                    typing_data,
                    exclude_participant=participant_id
                )

        except Exception as e:
            await self._send_error(websocket, f"Failed to handle typing indicator: {str(e)}")

    async def _send_error(self, websocket: WebSocket, error_message: str):
        """클라이언트에 에러 메시지 전송"""
        error_data = {
            "type": "error",
            "message": error_message
        }
        try:
            await websocket.send_text(json.dumps(error_data))
        except Exception:
            pass  # 연결이 이미 끊어진 경우
```

## 3. WebSocket 엔드포인트

### app/api/v1/websocket.py

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import uuid

from app.database import get_db
from app.websocket.manager import manager
from app.websocket.handlers import WebSocketHandler
from app.services.participant_service import ParticipantService
from app.services.session_service import SessionService

router = APIRouter()

@router.websocket("/ws/{session_code}/{participant_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_code: str,
    participant_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket 연결 엔드포인트"""

    # 세션과 참가자 유효성 검사
    session_service = SessionService(db)
    participant_service = ParticipantService(db)

    session = session_service.get_session_by_code(session_code)
    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return

    try:
        participant_uuid = uuid.UUID(participant_id)
        participant = participant_service.get_participant_by_id(participant_uuid)
        if not participant or participant.session_id != session.id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Participant not found")
            return
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid participant ID")
        return

    # WebSocket 연결 수락
    await manager.connect(websocket, session_code, participant_id)

    # 웹소켓 핸들러 초기화
    handler = WebSocketHandler(db)

    try:
        # 참가자 온라인 상태 업데이트
        participant_service.update_participant_status(participant_uuid, is_online=True)

        while True:
            # 메시지 수신 대기
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 메시지 처리
            await handler.handle_message(websocket, message_data, participant_id)

    except WebSocketDisconnect:
        # 연결 해제 처리
        manager.disconnect(participant_id)

        # 참가자 오프라인 상태 업데이트
        participant_service.update_participant_status(participant_uuid, is_online=False)

        # 다른 참가자들에게 알림
        await manager.broadcast_to_session(session_code, {
            "type": "participant_left",
            "participant_id": participant_id,
            "message": f"{participant.nickname}님이 떠났습니다."
        })

    except Exception as e:
        # 예상치 못한 오류 처리
        manager.disconnect(participant_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")

@router.get("/sessions/{session_code}/status")
async def get_session_status(
    session_code: str,
    db: Session = Depends(get_db)
):
    """세션 실시간 상태 조회"""
    session_service = SessionService(db)
    session = session_service.get_session_by_code(session_code)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    online_participants = manager.get_session_participants(session_code)
    participant_count = manager.get_participant_count(session_code)

    return {
        "session_code": session_code,
        "status": session.status,
        "online_participants": online_participants,
        "online_count": participant_count,
        "total_participants": len(session.participants)
    }
```

## 4. 메시지 서비스 확장

### app/services/message_service.py (추가 메서드)

```python
from datetime import datetime
from typing import Optional

class MessageService:
    # ... 기존 코드 ...

    def send_message(self, message_data: MessageCreate, participant_id: Optional[str] = None) -> Message:
        """메시지 전송 (WebSocket용)"""
        message = Message(
            content=message_data.content,
            message_type=message_data.message_type,
            session_id=message_data.session_id,
            participant_id=participant_id if participant_id else None
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_recent_messages(self, session_id: uuid.UUID, limit: int = 50) -> List[Message]:
        """최근 메시지 조회"""
        return self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

class ParticipantService:
    # ... 기존 코드 ...

    def update_participant_status(self, participant_id: uuid.UUID, is_online: bool):
        """참가자 온라인 상태 업데이트"""
        participant = self.get_participant_by_id(participant_id)
        if participant:
            participant.is_online = is_online
            participant.last_seen = datetime.utcnow()
            self.db.commit()
```