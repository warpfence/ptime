"""
실시간 참여자 모니터링 서비스
"""

import json
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from ..core.redis_client import RedisClient, get_redis
from ..models.participant import Participant
from sqlalchemy.orm import Session


class ParticipantMonitor:
    """Redis 기반 실시간 참여자 모니터링 서비스"""

    def __init__(self, redis_client: RedisClient = None):
        self.redis = redis_client or get_redis()
        self.default_ttl = 300  # 5분 기본 TTL
        self.heartbeat_interval = 30  # 30초 하트비트 간격

    def _get_session_key(self, session_id: str) -> str:
        """세션별 참여자 관리 키 생성"""
        return f"session:{session_id}:participants"

    def _get_participant_key(self, participant_id: str) -> str:
        """참여자별 상태 관리 키 생성"""
        return f"participant:{participant_id}:status"

    def _get_session_stats_key(self, session_id: str) -> str:
        """세션 통계 키 생성"""
        return f"session:{session_id}:stats"

    def _get_activity_key(self, participant_id: str) -> str:
        """참여자 활동 추적 키 생성"""
        return f"participant:{participant_id}:activity"

    def add_participant(
        self,
        session_id: str,
        participant_id: str,
        participant_data: Dict
    ) -> bool:
        """
        세션에 참여자 추가

        Args:
            session_id: 세션 ID
            participant_id: 참여자 ID
            participant_data: 참여자 정보 (닉네임, IP 등)

        Returns:
            추가 성공 여부
        """
        try:
            session_key = self._get_session_key(session_id)
            participant_key = self._get_participant_key(participant_id)
            stats_key = self._get_session_stats_key(session_id)

            # 참여자를 세션 참여자 Set에 추가
            self.redis.sadd(session_key, participant_id)
            self.redis.expire(session_key, self.default_ttl)

            # 참여자 상태 정보 저장
            participant_status = {
                **participant_data,
                "session_id": session_id,
                "joined_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "is_online": True
            }
            self.redis.set(participant_key, participant_status, ex=self.default_ttl)

            # 세션 통계 업데이트
            self._update_session_stats(session_id)

            # 활동 추적 시작
            self._track_activity(participant_id, "joined")

            return True

        except Exception as e:
            print(f"참여자 추가 오류: {e}")
            return False

    def remove_participant(self, session_id: str, participant_id: str) -> bool:
        """
        세션에서 참여자 제거

        Args:
            session_id: 세션 ID
            participant_id: 참여자 ID

        Returns:
            제거 성공 여부
        """
        try:
            session_key = self._get_session_key(session_id)
            participant_key = self._get_participant_key(participant_id)
            activity_key = self._get_activity_key(participant_id)

            # 세션 참여자 Set에서 제거
            self.redis.srem(session_key, participant_id)

            # 참여자 상태 정보 삭제
            self.redis.delete(participant_key)

            # 활동 기록 삭제
            self.redis.delete(activity_key)

            # 세션 통계 업데이트
            self._update_session_stats(session_id)

            # 활동 추적
            self._track_activity(participant_id, "left")

            return True

        except Exception as e:
            print(f"참여자 제거 오류: {e}")
            return False

    def update_heartbeat(self, participant_id: str) -> bool:
        """
        참여자 하트비트 업데이트

        Args:
            participant_id: 참여자 ID

        Returns:
            업데이트 성공 여부
        """
        try:
            participant_key = self._get_participant_key(participant_id)

            # 참여자 상태 조회
            participant_status = self.redis.get(participant_key)
            if not participant_status:
                return False

            # 마지막 활동 시간 업데이트
            participant_status["last_seen"] = datetime.utcnow().isoformat()
            participant_status["is_online"] = True

            # Redis에 저장 (TTL 연장)
            self.redis.set(participant_key, participant_status, ex=self.default_ttl)

            # 활동 추적
            self._track_activity(participant_id, "heartbeat")

            return True

        except Exception as e:
            print(f"하트비트 업데이트 오류: {e}")
            return False

    def get_session_participants(self, session_id: str) -> List[Dict]:
        """
        세션의 모든 참여자 조회

        Args:
            session_id: 세션 ID

        Returns:
            참여자 목록
        """
        try:
            session_key = self._get_session_key(session_id)
            participant_ids = self.redis.smembers(session_key)

            participants = []
            for participant_id in participant_ids:
                participant_key = self._get_participant_key(participant_id)
                participant_data = self.redis.get(participant_key)

                if participant_data:
                    # 온라인 상태 확인
                    last_seen = datetime.fromisoformat(participant_data["last_seen"])
                    is_online = (datetime.utcnow() - last_seen).total_seconds() < self.default_ttl

                    participant_data["id"] = participant_id
                    participant_data["is_online"] = is_online
                    participants.append(participant_data)

            return participants

        except Exception as e:
            print(f"참여자 목록 조회 오류: {e}")
            return []

    def get_participant_count(self, session_id: str) -> int:
        """
        세션 참여자 수 조회

        Args:
            session_id: 세션 ID

        Returns:
            참여자 수
        """
        try:
            session_key = self._get_session_key(session_id)
            return self.redis.scard(session_key)
        except Exception as e:
            print(f"참여자 수 조회 오류: {e}")
            return 0

    def get_online_participant_count(self, session_id: str) -> int:
        """
        온라인 참여자 수 조회

        Args:
            session_id: 세션 ID

        Returns:
            온라인 참여자 수
        """
        try:
            participants = self.get_session_participants(session_id)
            return len([p for p in participants if p.get("is_online", False)])
        except Exception as e:
            print(f"온라인 참여자 수 조회 오류: {e}")
            return 0

    def cleanup_inactive_participants(self, session_id: str) -> int:
        """
        비활성 참여자 자동 제거

        Args:
            session_id: 세션 ID

        Returns:
            제거된 참여자 수
        """
        try:
            session_key = self._get_session_key(session_id)
            participant_ids = self.redis.smembers(session_key)

            removed_count = 0
            current_time = datetime.utcnow()

            for participant_id in participant_ids:
                participant_key = self._get_participant_key(participant_id)
                participant_data = self.redis.get(participant_key)

                if not participant_data:
                    # 데이터가 없으면 Set에서 제거
                    self.redis.srem(session_key, participant_id)
                    removed_count += 1
                    continue

                # TTL 만료 확인
                last_seen = datetime.fromisoformat(participant_data["last_seen"])
                inactive_duration = (current_time - last_seen).total_seconds()

                if inactive_duration > self.default_ttl:
                    self.remove_participant(session_id, participant_id)
                    removed_count += 1

            # 세션 통계 업데이트
            if removed_count > 0:
                self._update_session_stats(session_id)

            return removed_count

        except Exception as e:
            print(f"비활성 참여자 정리 오류: {e}")
            return 0

    def get_session_stats(self, session_id: str) -> Dict:
        """
        세션 통계 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 통계 정보
        """
        try:
            stats_key = self._get_session_stats_key(session_id)
            stats = self.redis.get(stats_key) or {}

            # 실시간 정보 업데이트
            stats.update({
                "current_participants": self.get_participant_count(session_id),
                "online_participants": self.get_online_participant_count(session_id),
                "last_updated": datetime.utcnow().isoformat()
            })

            return stats

        except Exception as e:
            print(f"세션 통계 조회 오류: {e}")
            return {}

    def _update_session_stats(self, session_id: str):
        """세션 통계 업데이트"""
        try:
            stats_key = self._get_session_stats_key(session_id)
            current_stats = self.redis.get(stats_key) or {}

            # 현재 상태 업데이트
            current_stats.update({
                "total_participants": self.get_participant_count(session_id),
                "online_participants": self.get_online_participant_count(session_id),
                "last_updated": datetime.utcnow().isoformat()
            })

            # 최대 참여자 수 추적
            current_count = current_stats["total_participants"]
            max_participants = current_stats.get("max_participants", 0)
            if current_count > max_participants:
                current_stats["max_participants"] = current_count

            self.redis.set(stats_key, current_stats, ex=3600)  # 1시간 TTL

        except Exception as e:
            print(f"세션 통계 업데이트 오류: {e}")

    def _track_activity(self, participant_id: str, activity_type: str):
        """참여자 활동 추적"""
        try:
            activity_key = self._get_activity_key(participant_id)

            activity_log = {
                "type": activity_type,
                "timestamp": datetime.utcnow().isoformat()
            }

            # 최근 활동 로그 저장 (최대 100개)
            activities = self.redis.get(activity_key) or []
            activities.append(activity_log)

            # 최근 100개 활동만 유지
            if len(activities) > 100:
                activities = activities[-100:]

            self.redis.set(activity_key, activities, ex=3600)  # 1시간 TTL

        except Exception as e:
            print(f"활동 추적 오류: {e}")

    def get_participant_activities(self, participant_id: str) -> List[Dict]:
        """참여자 활동 기록 조회"""
        try:
            activity_key = self._get_activity_key(participant_id)
            return self.redis.get(activity_key) or []
        except Exception as e:
            print(f"활동 기록 조회 오류: {e}")
            return []

    def is_participant_online(self, participant_id: str) -> bool:
        """참여자 온라인 상태 확인"""
        try:
            participant_key = self._get_participant_key(participant_id)
            participant_data = self.redis.get(participant_key)

            if not participant_data:
                return False

            last_seen = datetime.fromisoformat(participant_data["last_seen"])
            return (datetime.utcnow() - last_seen).total_seconds() < self.default_ttl

        except Exception as e:
            print(f"온라인 상태 확인 오류: {e}")
            return False

    def get_all_sessions_stats(self) -> Dict[str, Dict]:
        """모든 세션의 통계 조회"""
        try:
            stats_keys = self.redis.keys("session:*:stats")
            all_stats = {}

            for key in stats_keys:
                session_id = key.split(":")[1]
                all_stats[session_id] = self.get_session_stats(session_id)

            return all_stats

        except Exception as e:
            print(f"전체 세션 통계 조회 오류: {e}")
            return {}


# 싱글톤 인스턴스
participant_monitor = ParticipantMonitor()


def get_participant_monitor() -> ParticipantMonitor:
    """참여자 모니터 의존성 주입용 함수"""
    return participant_monitor