# WebSocket 채팅 시스템 템플릿

## 1. Socket.io 서버 설정

### app/websocket/server.py
```python
import socketio
import json
from typing import Dict
from sqlalchemy.orm import sessionmaker
from ..database import engine
from ..services.realtime import RealtimeService
from ..models.chat import ChatMessage, MessageType
from ..models.participant import Participant

# Socket.io 서버 생성
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

SessionLocal = sessionmaker(bind=engine)

class SocketManager:
    def __init__(self):
        self.realtime_service = RealtimeService()
        self.connected_clients: Dict[str, Dict] = {}

    async def handle_connect(self, sid: str, environ: dict):
        """클라이언트 연결 처리"""
        print(f"Client {sid} connected")
        await sio.emit('connected', {'status': 'connected'}, room=sid)

    async def handle_disconnect(self, sid: str):
        """클라이언트 연결 해제 처리"""
        if sid in self.connected_clients:
            client_info = self.connected_clients[sid]
            session_id = client_info.get('session_id')

            if session_id:
                # 세션에서 제거
                await sio.leave_room(sid, f"session_{session_id}")

                # 참여자 수 업데이트 브로드캐스트
                count = self.realtime_service.get_participant_count(session_id)
                await sio.emit('participant_count_update',
                             {'count': count},
                             room=f"session_{session_id}")

            del self.connected_clients[sid]

    async def handle_join_session(self, sid: str, data: dict):
        """세션 참여 처리"""
        session_id = data.get('session_id')
        participant_id = data.get('participant_id')
        nickname = data.get('nickname')
        role = data.get('role', 'participant')  # participant 또는 presenter

        if not all([session_id, nickname]):
            await sio.emit('error', {'message': '필수 데이터가 누락되었습니다.'}, room=sid)
            return

        # 클라이언트 정보 저장
        self.connected_clients[sid] = {
            'session_id': session_id,
            'participant_id': participant_id,
            'nickname': nickname,
            'role': role
        }

        # 세션 룸에 참여
        await sio.enter_room(sid, f"session_{session_id}")

        # 참여자인 경우 실시간 참여자에 추가
        if role == 'participant' and participant_id:
            self.realtime_service.add_participant(session_id, participant_id, nickname)

        # 참여자 수 업데이트 브로드캐스트
        count = self.realtime_service.get_participant_count(session_id)
        await sio.emit('participant_count_update',
                     {'count': count},
                     room=f"session_{session_id}")

        await sio.emit('joined_session',
                     {'session_id': session_id, 'participant_count': count},
                     room=sid)

    async def handle_send_message(self, sid: str, data: dict):
        """채팅 메시지 전송"""
        if sid not in self.connected_clients:
            await sio.emit('error', {'message': '세션에 참여하지 않았습니다.'}, room=sid)
            return

        client_info = self.connected_clients[sid]
        session_id = client_info['session_id']
        participant_id = client_info.get('participant_id')
        nickname = client_info['nickname']

        message_text = data.get('message', '').strip()
        message_type = data.get('message_type', 'text')

        if not message_text:
            await sio.emit('error', {'message': '메시지가 비어있습니다.'}, room=sid)
            return

        # 데이터베이스에 메시지 저장
        db = SessionLocal()
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                participant_id=participant_id,
                message=message_text,
                message_type=MessageType(message_type)
            )
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)

            # 세션 룸에 메시지 브로드캐스트
            message_data = {
                'id': str(chat_message.id),
                'participant_nickname': nickname,
                'message': chat_message.message,
                'message_type': chat_message.message_type.value,
                'created_at': chat_message.created_at.isoformat()
            }

            await sio.emit('new_message', message_data, room=f"session_{session_id}")

        except Exception as e:
            await sio.emit('error', {'message': '메시지 전송에 실패했습니다.'}, room=sid)
        finally:
            db.close()

    async def handle_get_chat_history(self, sid: str, data: dict):
        """채팅 히스토리 조회"""
        if sid not in self.connected_clients:
            return

        client_info = self.connected_clients[sid]
        session_id = client_info['session_id']

        db = SessionLocal()
        try:
            messages = db.query(ChatMessage, Participant.nickname).join(
                Participant, ChatMessage.participant_id == Participant.id, isouter=True
            ).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(50).all()

            history = []
            for message, nickname in messages:
                history.append({
                    'id': str(message.id),
                    'participant_nickname': nickname,
                    'message': message.message,
                    'message_type': message.message_type.value,
                    'created_at': message.created_at.isoformat()
                })

            await sio.emit('chat_history', {'messages': list(reversed(history))}, room=sid)

        finally:
            db.close()

# 전역 매니저 인스턴스
socket_manager = SocketManager()

# 이벤트 핸들러 등록
@sio.event
async def connect(sid, environ):
    await socket_manager.handle_connect(sid, environ)

@sio.event
async def disconnect(sid):
    await socket_manager.handle_disconnect(sid)

@sio.event
async def join_session(sid, data):
    await socket_manager.handle_join_session(sid, data)

@sio.event
async def send_message(sid, data):
    await socket_manager.handle_send_message(sid, data)

@sio.event
async def get_chat_history(sid, data):
    await socket_manager.handle_get_chat_history(sid, data)
```

## 2. 실시간 서비스

### app/services/realtime.py
```python
import redis
import json
from typing import Dict, List
from datetime import datetime, timedelta
from ..config import settings

class RealtimeService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.redis_url)
        self.participant_ttl = 300  # 5분 TTL

    def add_participant(self, session_id: str, participant_id: str, nickname: str):
        """실시간 참여자 추가"""
        key = f"session:{session_id}:participants"
        participant_data = {
            "id": participant_id,
            "nickname": nickname,
            "joined_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }

        self.redis_client.hset(key, participant_id, json.dumps(participant_data))
        self.redis_client.expire(key, self.participant_ttl)

    def update_participant_activity(self, session_id: str, participant_id: str):
        """참여자 활동 시간 업데이트"""
        key = f"session:{session_id}:participants"
        participant_data = self.redis_client.hget(key, participant_id)

        if participant_data:
            data = json.loads(participant_data)
            data["last_seen"] = datetime.now().isoformat()
            self.redis_client.hset(key, participant_id, json.dumps(data))

    def remove_participant(self, session_id: str, participant_id: str):
        """참여자 제거"""
        key = f"session:{session_id}:participants"
        self.redis_client.hdel(key, participant_id)

    def get_active_participants(self, session_id: str) -> List[Dict]:
        """활성 참여자 목록 조회"""
        key = f"session:{session_id}:participants"
        participants_data = self.redis_client.hgetall(key)

        active_participants = []
        cutoff_time = datetime.now() - timedelta(minutes=2)

        for participant_id, data in participants_data.items():
            participant = json.loads(data)
            last_seen = datetime.fromisoformat(participant["last_seen"])

            if last_seen > cutoff_time:
                active_participants.append(participant)
            else:
                # 비활성 참여자 제거
                self.redis_client.hdel(key, participant_id)

        return active_participants

    def get_participant_count(self, session_id: str) -> int:
        """실시간 참여자 수 조회"""
        return len(self.get_active_participants(session_id))

    def set_session_state(self, session_id: str, state: dict):
        """세션 상태 저장"""
        key = f"session:{session_id}:state"
        self.redis_client.set(key, json.dumps(state), ex=3600)  # 1시간 TTL

    def get_session_state(self, session_id: str) -> dict:
        """세션 상태 조회"""
        key = f"session:{session_id}:state"
        state_data = self.redis_client.get(key)
        return json.loads(state_data) if state_data else {}
```

## 3. 채팅 스키마

### app/schemas/chat.py
```python
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from ..models.chat import MessageType

class ChatMessageCreate(BaseModel):
    message: str
    message_type: MessageType = MessageType.TEXT

    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('메시지는 비어있을 수 없습니다.')
        if len(v) > 500:
            raise ValueError('메시지는 500자를 초과할 수 없습니다.')
        return v.strip()

class ChatMessageResponse(BaseModel):
    id: str
    participant_nickname: Optional[str]
    message: str
    message_type: MessageType
    created_at: datetime

    class Config:
        orm_mode = True

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total_count: int
```

## 4. 참여자 시스템

### app/schemas/participant.py
```python
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class ParticipantJoin(BaseModel):
    nickname: str

    @validator('nickname')
    def validate_nickname(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('닉네임은 2글자 이상이어야 합니다.')
        if len(v.strip()) > 20:
            raise ValueError('닉네임은 20글자 이하여야 합니다.')
        # 특수문자 제한
        if not v.strip().replace(' ', '').isalnum():
            raise ValueError('닉네임은 한글, 영문, 숫자, 공백만 사용할 수 있습니다.')
        return v.strip()

class ParticipantResponse(BaseModel):
    id: str
    nickname: str
    joined_at: datetime
    is_online: bool = True

    class Config:
        orm_mode = True

class JoinSessionResponse(BaseModel):
    participant: ParticipantResponse
    session: dict
    message: str = "성공적으로 세션에 참여했습니다."
```

### app/services/participant.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.participant import Participant
from ..models.session import Session as SessionModel
from ..schemas.participant import ParticipantJoin
from fastapi import HTTPException

class ParticipantService:
    def __init__(self, db: Session):
        self.db = db

    def join_session(self, session_code: str, participant_data: ParticipantJoin, ip_address: str):
        # 세션 존재 및 활성 상태 확인
        session = self.db.query(SessionModel).filter(
            SessionModel.session_code == session_code,
            SessionModel.is_active == True
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 비활성 상태입니다.")

        # 동일 세션에서 닉네임 중복 확인
        existing = self.db.query(Participant).filter(
            Participant.session_id == session.id,
            Participant.nickname == participant_data.nickname
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="이미 사용중인 닉네임입니다.")

        # 참여자 생성
        participant = Participant(
            session_id=session.id,
            nickname=participant_data.nickname,
            ip_address=ip_address
        )

        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)

        return participant, session

    def get_session_participants(self, session_id: str):
        return self.db.query(Participant).filter(
            Participant.session_id == session_id
        ).order_by(Participant.joined_at.desc()).all()

    def update_last_seen(self, participant_id: str):
        participant = self.db.query(Participant).filter(Participant.id == participant_id).first()
        if participant:
            participant.last_seen = func.now()
            self.db.commit()
```

### app/api/participants.py
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.participant import ParticipantService
from ..schemas.participant import ParticipantJoin, JoinSessionResponse

router = APIRouter()

@router.post("/join/{session_code}", response_model=JoinSessionResponse)
def join_session(
    session_code: str,
    participant_data: ParticipantJoin,
    request: Request,
    db: Session = Depends(get_db)
):
    service = ParticipantService(db)
    ip_address = request.client.host

    participant, session = service.join_session(session_code, participant_data, ip_address)

    return {
        "participant": participant,
        "session": {
            "id": str(session.id),
            "title": session.title,
            "session_code": session.session_code
        }
    }
```