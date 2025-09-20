"""
채팅 메시지 서비스
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
import uuid
import hashlib

from ..models.message import Message
from ..schemas.message import MessageCreate, MessageUpdate, MessageResponse, MessageListResponse, MessageStats
from ..core.redis_client import get_redis
from loguru import logger


class MessageService:
    """채팅 메시지 관리 서비스"""

    def __init__(self):
        self.redis = get_redis()
        self.message_cache_ttl = 3600  # 1시간
        self.recent_messages_key = "recent_messages"

    def generate_message_id(self, session_id: str, participant_id: str, content: str) -> str:
        """고유한 메시지 ID 생성"""
        timestamp = datetime.utcnow().timestamp()
        raw_data = f"{session_id}:{participant_id}:{content}:{timestamp}"
        hash_part = hashlib.md5(raw_data.encode()).hexdigest()[:8]
        return f"msg_{timestamp}_{hash_part}"

    async def create_message(
        self,
        db: Session,
        message_data: MessageCreate,
        store_in_db: bool = True
    ) -> Dict[str, Any]:
        """
        새 메시지 생성

        Args:
            db: 데이터베이스 세션
            message_data: 메시지 데이터
            store_in_db: 데이터베이스 저장 여부

        Returns:
            생성된 메시지 정보
        """
        try:
            # 메시지 ID 생성
            message_id = self.generate_message_id(
                message_data.session_id,
                message_data.participant_id,
                message_data.content
            )

            # 메시지 객체 생성
            db_message = Message(
                id=message_id,
                session_id=message_data.session_id,
                participant_id=message_data.participant_id,
                nickname=message_data.nickname,
                content=message_data.content,
                message_type=message_data.message_type.value,
                ip_address=message_data.ip_address,
                user_agent=message_data.user_agent
            )

            # 데이터베이스 저장
            if store_in_db:
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
                logger.info(f"메시지 데이터베이스 저장 완료: {message_id}")

            # Redis 캐시 저장 (최근 메시지)
            await self._cache_recent_message(db_message)

            # WebSocket 전송용 데이터 반환
            return db_message.to_websocket_format()

        except Exception as e:
            logger.error(f"메시지 생성 오류: {e}")
            if store_in_db:
                db.rollback()
            raise

    async def get_message(self, db: Session, message_id: str) -> Optional[MessageResponse]:
        """메시지 단건 조회"""
        try:
            # Redis 캐시 확인
            cached_message = await self._get_cached_message(message_id)
            if cached_message:
                return cached_message

            # 데이터베이스 조회
            message = db.query(Message).filter(
                Message.id == message_id,
                Message.is_deleted == False
            ).first()

            if not message:
                return None

            # 캐시 저장
            await self._cache_message(message)

            return MessageResponse.from_orm(message)

        except Exception as e:
            logger.error(f"메시지 조회 오류: {e}")
            return None

    async def get_session_messages(
        self,
        db: Session,
        session_id: str,
        page: int = 1,
        page_size: int = 50,
        order: str = "desc"
    ) -> MessageListResponse:
        """세션의 메시지 목록 조회"""
        try:
            # 오프셋 계산
            offset = (page - 1) * page_size

            # 정렬 순서 설정
            order_by = desc(Message.created_at) if order == "desc" else asc(Message.created_at)

            # 메시지 조회
            query = db.query(Message).filter(
                Message.session_id == session_id,
                Message.is_deleted == False
            )

            total_count = query.count()
            messages = query.order_by(order_by).offset(offset).limit(page_size).all()

            # 응답 데이터 구성
            message_responses = []
            for message in messages:
                message_data = message.to_dict()
                message_responses.append(MessageResponse(**message_data))

            has_next = (page * page_size) < total_count

            return MessageListResponse(
                messages=message_responses,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next
            )

        except Exception as e:
            logger.error(f"세션 메시지 목록 조회 오류: {e}")
            return MessageListResponse(
                messages=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False
            )

    async def get_recent_messages(
        self,
        db: Session,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """최근 메시지 조회 (캐시 우선)"""
        try:
            # Redis에서 최근 메시지 조회
            cached_messages = await self._get_cached_recent_messages(session_id, limit)
            if cached_messages:
                return cached_messages

            # 데이터베이스에서 조회
            messages = db.query(Message).filter(
                Message.session_id == session_id,
                Message.is_deleted == False
            ).order_by(desc(Message.created_at)).limit(limit).all()

            # WebSocket 포맷으로 변환
            result = [message.to_websocket_format() for message in messages]

            # 캐시 저장
            await self._cache_recent_messages(session_id, result)

            return result

        except Exception as e:
            logger.error(f"최근 메시지 조회 오류: {e}")
            return []

    async def update_message(
        self,
        db: Session,
        message_id: str,
        participant_id: str,
        update_data: MessageUpdate
    ) -> Optional[MessageResponse]:
        """메시지 수정"""
        try:
            # 메시지 조회
            message = db.query(Message).filter(
                Message.id == message_id,
                Message.participant_id == participant_id,
                Message.is_deleted == False
            ).first()

            if not message:
                return None

            # 수정
            message.content = update_data.content
            message.is_edited = True
            message.edit_count += 1
            message.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(message)

            # 캐시 갱신
            await self._cache_message(message)
            await self._invalidate_recent_messages_cache(message.session_id)

            logger.info(f"메시지 수정 완료: {message_id}")
            return MessageResponse.from_orm(message)

        except Exception as e:
            logger.error(f"메시지 수정 오류: {e}")
            db.rollback()
            return None

    async def delete_message(
        self,
        db: Session,
        message_id: str,
        participant_id: str
    ) -> bool:
        """메시지 삭제 (소프트 삭제)"""
        try:
            # 메시지 조회
            message = db.query(Message).filter(
                Message.id == message_id,
                Message.participant_id == participant_id,
                Message.is_deleted == False
            ).first()

            if not message:
                return False

            # 소프트 삭제
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()

            db.commit()

            # 캐시 삭제
            await self._remove_cached_message(message_id)
            await self._invalidate_recent_messages_cache(message.session_id)

            logger.info(f"메시지 삭제 완료: {message_id}")
            return True

        except Exception as e:
            logger.error(f"메시지 삭제 오류: {e}")
            db.rollback()
            return False

    async def get_message_stats(self, db: Session, session_id: str) -> MessageStats:
        """메시지 통계 조회"""
        try:
            # 캐시 확인
            cached_stats = await self._get_cached_stats(session_id)
            if cached_stats:
                return cached_stats

            # 통계 계산
            stats_query = db.query(
                func.count(Message.id).label('total_messages'),
                func.count(func.distinct(Message.participant_id)).label('total_participants'),
                func.min(Message.created_at).label('first_message_at'),
                func.max(Message.created_at).label('last_message_at')
            ).filter(
                Message.session_id == session_id,
                Message.is_deleted == False
            ).first()

            total_messages = stats_query.total_messages or 0
            total_participants = stats_query.total_participants or 0
            messages_per_participant = (
                total_messages / total_participants if total_participants > 0 else 0
            )

            stats = MessageStats(
                session_id=session_id,
                total_messages=total_messages,
                total_participants=total_participants,
                messages_per_participant=round(messages_per_participant, 2),
                first_message_at=stats_query.first_message_at,
                last_message_at=stats_query.last_message_at
            )

            # 캐시 저장 (5분)
            await self._cache_stats(session_id, stats)

            return stats

        except Exception as e:
            logger.error(f"메시지 통계 조회 오류: {e}")
            return MessageStats(
                session_id=session_id,
                total_messages=0,
                total_participants=0,
                messages_per_participant=0.0,
                first_message_at=None,
                last_message_at=None
            )

    # Redis 캐시 메서드들
    async def _cache_message(self, message: Message):
        """메시지 캐시 저장"""
        try:
            key = f"message:{message.id}"
            data = message.to_dict()
            self.redis.set(key, data, ex=self.message_cache_ttl)
        except Exception as e:
            logger.error(f"메시지 캐시 저장 오류: {e}")

    async def _get_cached_message(self, message_id: str) -> Optional[MessageResponse]:
        """캐시된 메시지 조회"""
        try:
            key = f"message:{message_id}"
            data = self.redis.get(key)
            if data:
                return MessageResponse(**data)
            return None
        except Exception as e:
            logger.error(f"캐시된 메시지 조회 오류: {e}")
            return None

    async def _remove_cached_message(self, message_id: str):
        """캐시된 메시지 삭제"""
        try:
            key = f"message:{message_id}"
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"캐시된 메시지 삭제 오류: {e}")

    async def _cache_recent_message(self, message: Message):
        """최근 메시지 캐시에 추가"""
        try:
            key = f"recent_messages:{message.session_id}"
            message_data = message.to_websocket_format()

            # 기존 최근 메시지 목록 조회
            cached_messages = self.redis.get(key) or []

            # 새 메시지를 맨 앞에 추가
            cached_messages.insert(0, message_data)

            # 최대 50개까지만 유지
            if len(cached_messages) > 50:
                cached_messages = cached_messages[:50]

            # 캐시 저장
            self.redis.set(key, cached_messages, ex=self.message_cache_ttl)

        except Exception as e:
            logger.error(f"최근 메시지 캐시 추가 오류: {e}")

    async def _get_cached_recent_messages(self, session_id: str, limit: int) -> Optional[List[Dict]]:
        """캐시된 최근 메시지 조회"""
        try:
            key = f"recent_messages:{session_id}"
            cached_messages = self.redis.get(key)
            if cached_messages:
                return cached_messages[:limit]
            return None
        except Exception as e:
            logger.error(f"캐시된 최근 메시지 조회 오류: {e}")
            return None

    async def _cache_recent_messages(self, session_id: str, messages: List[Dict]):
        """최근 메시지 목록 캐시 저장"""
        try:
            key = f"recent_messages:{session_id}"
            self.redis.set(key, messages, ex=self.message_cache_ttl)
        except Exception as e:
            logger.error(f"최근 메시지 목록 캐시 저장 오류: {e}")

    async def _invalidate_recent_messages_cache(self, session_id: str):
        """최근 메시지 캐시 무효화"""
        try:
            key = f"recent_messages:{session_id}"
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"최근 메시지 캐시 무효화 오류: {e}")

    async def _cache_stats(self, session_id: str, stats: MessageStats):
        """통계 캐시 저장"""
        try:
            key = f"message_stats:{session_id}"
            data = stats.dict()
            self.redis.set(key, data, ex=300)  # 5분
        except Exception as e:
            logger.error(f"통계 캐시 저장 오류: {e}")

    async def _get_cached_stats(self, session_id: str) -> Optional[MessageStats]:
        """캐시된 통계 조회"""
        try:
            key = f"message_stats:{session_id}"
            data = self.redis.get(key)
            if data:
                return MessageStats(**data)
            return None
        except Exception as e:
            logger.error(f"캐시된 통계 조회 오류: {e}")
            return None


# 싱글톤 인스턴스
message_service = MessageService()


def get_message_service() -> MessageService:
    """메시지 서비스 의존성 주입용 함수"""
    return message_service