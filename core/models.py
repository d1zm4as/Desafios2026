import uuid

from django.conf import settings
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    rating = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title


class Session(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='sessions')
    starts_at = models.DateTimeField()
    auditorium = models.CharField(max_length=100)
    total_rows = models.PositiveIntegerField(default=10)
    seats_per_row = models.PositiveIntegerField(default=12)

    class Meta:
        ordering = ['starts_at']

    def __str__(self) -> str:
        return f'{self.movie.title} @ {self.starts_at}'


class SessionSeat(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='seats')
    row = models.PositiveIntegerField()
    number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('session', 'row', 'number')
        ordering = ['row', 'number']

    def __str__(self) -> str:
        return f'S{self.session_id} R{self.row} N{self.number}'


class Ticket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    session_seat = models.OneToOneField(SessionSeat, on_delete=models.PROTECT, related_name='ticket')
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self) -> str:
        return f'{self.user_id}-{self.code}'
