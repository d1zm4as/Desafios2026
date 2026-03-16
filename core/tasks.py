import time

from celery import shared_task
from django.conf import settings
from redis import Redis

from core.locks import LOCK_INDEX_KEY


@shared_task
def cleanup_expired_locks() -> int:
    redis_client = Redis.from_url(settings.REDIS_URL)
    now = int(time.time())
    expired_keys = redis_client.zrangebyscore(LOCK_INDEX_KEY, 0, now)
    if not expired_keys:
        return 0
    deleted = 0
    for key in expired_keys:
        deleted += redis_client.delete(key)
    redis_client.zremrangebyscore(LOCK_INDEX_KEY, 0, now)
    return deleted


@shared_task
def send_ticket_confirmation_email(user_id: int, ticket_code: str) -> None:
    # Placeholder for email integration.
    return None
