"""
Redis 클라이언트 및 연결 관리
"""

import redis
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ..config import settings


class RedisClient:
    """Redis 클라이언트 래퍼 클래스"""

    def __init__(self):
        self.client = None
        self.connect()

    def connect(self):
        """Redis 서버에 연결"""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 연결 테스트
            self.client.ping()
            print(f"Redis 연결 성공: {settings.redis_url}")
        except Exception as e:
            print(f"Redis 연결 실패: {e}")
            # 개발 환경에서는 FakeRedis 사용 (선택사항)
            self.client = None

    def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            if self.client:
                self.client.ping()
                return True
        except:
            pass
        return False

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """키-값 설정 (TTL 포함)"""
        try:
            if not self.client:
                return False

            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            return self.client.set(key, value, ex=ex)
        except Exception as e:
            print(f"Redis SET 오류: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """키로 값 조회"""
        try:
            if not self.client:
                return None

            value = self.client.get(key)
            if value is None:
                return None

            # JSON 파싱 시도
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis GET 오류: {e}")
            return None

    def delete(self, *keys: str) -> int:
        """키 삭제"""
        try:
            if not self.client:
                return 0
            return self.client.delete(*keys)
        except Exception as e:
            print(f"Redis DELETE 오류: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            if not self.client:
                return False
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS 오류: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """키에 TTL 설정"""
        try:
            if not self.client:
                return False
            return self.client.expire(key, seconds)
        except Exception as e:
            print(f"Redis EXPIRE 오류: {e}")
            return False

    def ttl(self, key: str) -> int:
        """키의 남은 TTL 조회"""
        try:
            if not self.client:
                return -1
            return self.client.ttl(key)
        except Exception as e:
            print(f"Redis TTL 오류: {e}")
            return -1

    def sadd(self, key: str, *values: str) -> int:
        """Set에 값 추가"""
        try:
            if not self.client:
                return 0
            return self.client.sadd(key, *values)
        except Exception as e:
            print(f"Redis SADD 오류: {e}")
            return 0

    def srem(self, key: str, *values: str) -> int:
        """Set에서 값 제거"""
        try:
            if not self.client:
                return 0
            return self.client.srem(key, *values)
        except Exception as e:
            print(f"Redis SREM 오류: {e}")
            return 0

    def smembers(self, key: str) -> set:
        """Set의 모든 멤버 조회"""
        try:
            if not self.client:
                return set()
            return self.client.smembers(key)
        except Exception as e:
            print(f"Redis SMEMBERS 오류: {e}")
            return set()

    def scard(self, key: str) -> int:
        """Set의 크기 조회"""
        try:
            if not self.client:
                return 0
            return self.client.scard(key)
        except Exception as e:
            print(f"Redis SCARD 오류: {e}")
            return 0

    def sismember(self, key: str, value: str) -> bool:
        """Set에 값이 존재하는지 확인"""
        try:
            if not self.client:
                return False
            return self.client.sismember(key, value)
        except Exception as e:
            print(f"Redis SISMEMBER 오류: {e}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        """패턴으로 키 목록 조회"""
        try:
            if not self.client:
                return []
            return list(self.client.keys(pattern))
        except Exception as e:
            print(f"Redis KEYS 오류: {e}")
            return []

    def hset(self, key: str, field: str, value: Any) -> int:
        """Hash에 필드-값 설정"""
        try:
            if not self.client:
                return 0

            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            return self.client.hset(key, field, value)
        except Exception as e:
            print(f"Redis HSET 오류: {e}")
            return 0

    def hget(self, key: str, field: str) -> Optional[Any]:
        """Hash에서 필드 값 조회"""
        try:
            if not self.client:
                return None

            value = self.client.hget(key, field)
            if value is None:
                return None

            # JSON 파싱 시도
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis HGET 오류: {e}")
            return None

    def hgetall(self, key: str) -> Dict[str, Any]:
        """Hash의 모든 필드-값 조회"""
        try:
            if not self.client:
                return {}

            result = self.client.hgetall(key)
            parsed_result = {}

            for field, value in result.items():
                try:
                    parsed_result[field] = json.loads(value)
                except json.JSONDecodeError:
                    parsed_result[field] = value

            return parsed_result
        except Exception as e:
            print(f"Redis HGETALL 오류: {e}")
            return {}

    def hdel(self, key: str, *fields: str) -> int:
        """Hash에서 필드 삭제"""
        try:
            if not self.client:
                return 0
            return self.client.hdel(key, *fields)
        except Exception as e:
            print(f"Redis HDEL 오류: {e}")
            return 0


# 싱글톤 Redis 클라이언트 인스턴스
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Redis 클라이언트 의존성 주입용 함수"""
    return redis_client