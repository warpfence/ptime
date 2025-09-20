"""
WebSocket 연결 및 세션 관리 서비스
"""

import socketio
import json
from typing import Dict, Set, List, Optional
from datetime import datetime
from ..core.redis_client import get_redis
from ..services.participant_monitor import get_participant_monitor
from ..services.message_service import get_message_service
from ..schemas.message import MessageCreate, MessageType
from ..database import get_db
from loguru import logger


class WebSocketManager:
    """Socket.io 기반 WebSocket 연결 관리자"""

    def __init__(self):
        # Socket.io 서버 인스턴스 생성
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            async_mode='asgi'
        )

        self.redis = get_redis()
        self.participant_monitor = get_participant_monitor()
        self.message_service = get_message_service()

        # 연결 상태 관리
        self.active_connections: Dict[str, Dict] = {}  # sid -> connection_info
        self.session_rooms: Dict[str, Set[str]] = {}   # session_id -> set(sids)

        # 이벤트 핸들러 등록
        self._register_event_handlers()

    def _register_event_handlers(self):
        """Socket.io 이벤트 핸들러 등록"""

        @self.sio.event
        async def connect(sid, environ):
            """클라이언트 연결 이벤트"""
            logger.info(f"클라이언트 연결: {sid}")

            # 연결 정보 저장
            self.active_connections[sid] = {
                "connected_at": datetime.utcnow().isoformat(),
                "session_id": None,
                "participant_id": None,
                "nickname": None
            }

            # 연결 확인 메시지 전송
            await self.sio.emit("connected", {"message": "연결이 성공했습니다."}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """클라이언트 연결 해제 이벤트"""
            logger.info(f"클라이언트 연결 해제: {sid}")

            if sid in self.active_connections:
                connection_info = self.active_connections[sid]
                session_id = connection_info.get("session_id")
                participant_id = connection_info.get("participant_id")

                # 세션 룸에서 제거
                if session_id and session_id in self.session_rooms:
                    self.session_rooms[session_id].discard(sid)

                    # 세션 참여자 목록 업데이트 이벤트 전송
                    await self._emit_participant_count_update(session_id)

                # 참여자 모니터링에서 제거
                if session_id and participant_id:
                    self.participant_monitor.remove_participant(session_id, participant_id)

                # 연결 정보 제거
                del self.active_connections[sid]

        @self.sio.event
        async def join_session(sid, data):
            """세션 참여 이벤트"""
            try:
                session_id = data.get("session_id")
                participant_id = data.get("participant_id")
                nickname = data.get("nickname")

                if not all([session_id, participant_id, nickname]):
                    await self.sio.emit("error", {
                        "message": "필수 정보가 누락되었습니다."
                    }, room=sid)
                    return

                # 연결 정보 업데이트
                if sid in self.active_connections:
                    self.active_connections[sid].update({
                        "session_id": session_id,
                        "participant_id": participant_id,
                        "nickname": nickname
                    })

                # 세션 룸에 참가
                await self.sio.enter_room(sid, f"session_{session_id}")

                # 세션 룸 관리
                if session_id not in self.session_rooms:
                    self.session_rooms[session_id] = set()
                self.session_rooms[session_id].add(sid)

                # 참여자 모니터링에 추가
                participant_data = {
                    "nickname": nickname,
                    "ip_address": "websocket"  # WebSocket 연결은 IP 추적 어려움
                }
                self.participant_monitor.add_participant(session_id, participant_id, participant_data)

                # 세션 참여 성공 메시지
                await self.sio.emit("session_joined", {
                    "message": f"{nickname}님이 세션에 참여했습니다.",
                    "session_id": session_id,
                    "participant_id": participant_id
                }, room=sid)

                # 다른 참여자들에게 알림
                await self.sio.emit("participant_joined", {
                    "participant_id": participant_id,
                    "nickname": nickname,
                    "joined_at": datetime.utcnow().isoformat()
                }, room=f"session_{session_id}", skip_sid=sid)

                # 참여자 수 업데이트
                await self._emit_participant_count_update(session_id)

                logger.info(f"참여자 {nickname}({participant_id})가 세션 {session_id}에 참여")

            except Exception as e:
                logger.error(f"세션 참여 오류: {e}")
                await self.sio.emit("error", {
                    "message": "세션 참여 중 오류가 발생했습니다."
                }, room=sid)

        @self.sio.event
        async def leave_session(sid, data):
            """세션 나가기 이벤트"""
            try:
                if sid not in self.active_connections:
                    return

                connection_info = self.active_connections[sid]
                session_id = connection_info.get("session_id")
                participant_id = connection_info.get("participant_id")
                nickname = connection_info.get("nickname")

                if session_id:
                    # 세션 룸에서 나가기
                    await self.sio.leave_room(sid, f"session_{session_id}")

                    # 세션 룸 관리에서 제거
                    if session_id in self.session_rooms:
                        self.session_rooms[session_id].discard(sid)

                    # 참여자 모니터링에서 제거
                    if participant_id:
                        self.participant_monitor.remove_participant(session_id, participant_id)

                    # 다른 참여자들에게 알림
                    if nickname:
                        await self.sio.emit("participant_left", {
                            "participant_id": participant_id,
                            "nickname": nickname,
                            "left_at": datetime.utcnow().isoformat()
                        }, room=f"session_{session_id}")

                    # 참여자 수 업데이트
                    await self._emit_participant_count_update(session_id)

                    # 연결 정보 초기화
                    self.active_connections[sid].update({
                        "session_id": None,
                        "participant_id": None,
                        "nickname": None
                    })

                    logger.info(f"참여자 {nickname}({participant_id})가 세션 {session_id}에서 나감")

            except Exception as e:
                logger.error(f"세션 나가기 오류: {e}")

        @self.sio.event
        async def heartbeat(sid, data):
            """하트비트 이벤트 - 참여자 활동 상태 업데이트"""
            try:
                if sid in self.active_connections:
                    connection_info = self.active_connections[sid]
                    participant_id = connection_info.get("participant_id")

                    if participant_id:
                        # 참여자 모니터링 하트비트 업데이트
                        self.participant_monitor.update_heartbeat(participant_id)

                        # 하트비트 응답
                        await self.sio.emit("heartbeat_ack", {
                            "timestamp": datetime.utcnow().isoformat()
                        }, room=sid)

            except Exception as e:
                logger.error(f"하트비트 처리 오류: {e}")

        @self.sio.event
        async def send_message(sid, data):
            """메시지 전송 이벤트"""
            try:
                if sid not in self.active_connections:
                    return

                connection_info = self.active_connections[sid]
                session_id = connection_info.get("session_id")
                participant_id = connection_info.get("participant_id")
                nickname = connection_info.get("nickname")

                if not session_id:
                    await self.sio.emit("error", {
                        "message": "세션에 참여하지 않았습니다."
                    }, room=sid)
                    return

                message_content = data.get("message", "").strip()
                if not message_content:
                    return

                # 메시지 저장을 위한 데이터 생성
                message_create = MessageCreate(
                    session_id=session_id,
                    participant_id=participant_id,
                    nickname=nickname,
                    content=message_content,
                    message_type=MessageType.USER_MESSAGE,
                    ip_address="websocket"  # WebSocket에서는 IP 추적이 어려움
                )

                # 데이터베이스 세션 가져오기
                db = next(get_db())

                try:
                    # 메시지 저장 및 WebSocket 데이터 생성
                    websocket_data = await self.message_service.create_message(
                        db=db,
                        message_data=message_create,
                        store_in_db=True
                    )

                    # 세션의 모든 참여자에게 메시지 전송
                    await self.sio.emit("new_message", websocket_data, room=f"session_{session_id}")

                    # 참여자 활동 업데이트
                    self.participant_monitor.update_heartbeat(participant_id)

                    logger.info(f"메시지 저장 및 전송 완료: {nickname} -> {session_id}: {message_content}")

                except Exception as db_error:
                    logger.error(f"메시지 데이터베이스 저장 오류: {db_error}")

                    # 데이터베이스 저장이 실패해도 실시간 전송은 계속
                    fallback_data = {
                        "id": f"msg_{datetime.utcnow().timestamp()}",
                        "participant_id": participant_id,
                        "nickname": nickname,
                        "message": message_content,
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "user_message"
                    }

                    await self.sio.emit("new_message", fallback_data, room=f"session_{session_id}")
                    self.participant_monitor.update_heartbeat(participant_id)

                    logger.warning(f"폴백 메시지 전송: {nickname} -> {session_id}: {message_content}")

                finally:
                    db.close()

            except Exception as e:
                logger.error(f"메시지 전송 오류: {e}")

        @self.sio.event
        async def get_participant_list(sid, data):
            """참여자 목록 조회 이벤트"""
            try:
                if sid not in self.active_connections:
                    return

                connection_info = self.active_connections[sid]
                session_id = connection_info.get("session_id")

                if not session_id:
                    return

                # 참여자 목록 조회
                participants = self.participant_monitor.get_session_participants(session_id)

                # 참여자 목록 전송
                await self.sio.emit("participant_list", {
                    "participants": participants,
                    "total_count": len(participants),
                    "online_count": len([p for p in participants if p.get("is_online", False)])
                }, room=sid)

            except Exception as e:
                logger.error(f"참여자 목록 조회 오류: {e}")

    async def _emit_participant_count_update(self, session_id: str):
        """참여자 수 업데이트 이벤트 전송"""
        try:
            total_count = self.participant_monitor.get_participant_count(session_id)
            online_count = self.participant_monitor.get_online_participant_count(session_id)

            await self.sio.emit("participant_count_updated", {
                "session_id": session_id,
                "total_count": total_count,
                "online_count": online_count,
                "timestamp": datetime.utcnow().isoformat()
            }, room=f"session_{session_id}")

        except Exception as e:
            logger.error(f"참여자 수 업데이트 전송 오류: {e}")

    async def broadcast_to_session(self, session_id: str, event: str, data: dict):
        """특정 세션의 모든 참여자에게 메시지 브로드캐스트"""
        try:
            await self.sio.emit(event, data, room=f"session_{session_id}")
            logger.info(f"세션 {session_id}에 {event} 이벤트 브로드캐스트")
        except Exception as e:
            logger.error(f"브로드캐스트 오류: {e}")

    async def send_to_participant(self, session_id: str, participant_id: str, event: str, data: dict):
        """특정 참여자에게 메시지 전송"""
        try:
            # 참여자의 socket ID 찾기
            target_sid = None
            for sid, connection_info in self.active_connections.items():
                if (connection_info.get("session_id") == session_id and
                    connection_info.get("participant_id") == participant_id):
                    target_sid = sid
                    break

            if target_sid:
                await self.sio.emit(event, data, room=target_sid)
                logger.info(f"참여자 {participant_id}에게 {event} 이벤트 전송")
            else:
                logger.warning(f"참여자 {participant_id}의 연결을 찾을 수 없음")

        except Exception as e:
            logger.error(f"개별 전송 오류: {e}")

    def get_session_connections(self, session_id: str) -> List[Dict]:
        """세션의 활성 연결 목록 조회"""
        connections = []
        for sid, connection_info in self.active_connections.items():
            if connection_info.get("session_id") == session_id:
                connections.append({
                    "sid": sid,
                    **connection_info
                })
        return connections

    def get_total_connections(self) -> int:
        """전체 활성 연결 수"""
        return len(self.active_connections)

    def get_session_connection_count(self, session_id: str) -> int:
        """특정 세션의 연결 수"""
        return len(self.session_rooms.get(session_id, set()))


# 싱글톤 인스턴스
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """WebSocket 매니저 의존성 주입용 함수"""
    return websocket_manager