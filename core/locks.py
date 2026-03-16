import time
from typing import Dict, Tuple

import redis
from django.conf import settings

LOCK_TTL_SECONDS = 600
LOCK_KEY_PREFIX = 'seat_lock'
LOCK_INDEX_KEY = 'seat_lock_index'


def _redis() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL)


def _lock_key(session_id: int, seat_id: int) -> str:
    return f'{LOCK_KEY_PREFIX}:{session_id}:{seat_id}'


def acquire_lock(user_id: int, session_id: int, seat_id: int, ttl: int = LOCK_TTL_SECONDS) -> bool:
    redis_client = _redis()
    key = _lock_key(session_id, seat_id)
    expires_at = int(time.time()) + ttl
    value = f'{user_id}:{expires_at}'
    acquired = redis_client.set(key, value, nx=True, ex=ttl)
    if acquired:
        redis_client.zadd(LOCK_INDEX_KEY, {key: expires_at})
        return True

    existing = redis_client.get(key)
    if existing:
        existing_user = existing.decode().split(':', 1)[0]
        if str(existing_user) == str(user_id):
            redis_client.expire(key, ttl)
            redis_client.zadd(LOCK_INDEX_KEY, {key: expires_at})
            return True
    return False


def release_lock(user_id: int, session_id: int, seat_id: int) -> bool:
    redis_client = _redis()
    key = _lock_key(session_id, seat_id)
    existing = redis_client.get(key)
    if not existing:
        return False
    existing_user = existing.decode().split(':', 1)[0]
    if str(existing_user) != str(user_id):
        return False
    redis_client.delete(key)
    redis_client.zrem(LOCK_INDEX_KEY, key)
    return True


def is_locked_by_other(user_id: int, session_id: int, seat_id: int) -> bool:
    redis_client = _redis()
    key = _lock_key(session_id, seat_id)
    existing = redis_client.get(key)
    if not existing:
        return False
    existing_user = existing.decode().split(':', 1)[0]
    return str(existing_user) != str(user_id)


def is_locked_by_user(user_id: int, session_id: int, seat_id: int) -> bool:
    redis_client = _redis()
    key = _lock_key(session_id, seat_id)
    existing = redis_client.get(key)
    if not existing:
        return False
    existing_user = existing.decode().split(':', 1)[0]
    return str(existing_user) == str(user_id)


def get_session_locks(session_id: int) -> Dict[int, Tuple[int, int]]:
    redis_client = _redis()
    locks: Dict[int, Tuple[int, int]] = {}
    pattern = f'{LOCK_KEY_PREFIX}:{session_id}:*'
    for key in redis_client.scan_iter(match=pattern, count=1000):
        raw = redis_client.get(key)
        if not raw:
            continue
        user_str, expires_str = raw.decode().split(':', 1)
        seat_id = int(key.decode().split(':')[-1])
        locks[seat_id] = (int(user_str), int(expires_str))
    return locks
