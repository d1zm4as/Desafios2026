import logging
import time

from celery import shared_task
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from redis import Redis

from core.locks import LOCK_INDEX_KEY

logger = logging.getLogger(__name__)


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
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if not user or not user.email:
        logger.warning('Ticket email skipped for user_id=%s (missing user/email).', user_id)
        return None

    subject = 'Ticket confirmation'
    message = f'Your booking is confirmed. Ticket code: {ticket_code}.'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@cinepolis.local'
    send_mail(subject, message, from_email, [user.email], fail_silently=False)
    return None
