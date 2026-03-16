from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Session, SessionSeat


@receiver(post_save, sender=Session)
def create_session_seats(sender, instance: Session, created: bool, **kwargs) -> None:
    if not created:
        return
    seats = [
        SessionSeat(session=instance, row=row, number=number)
        for row in range(1, instance.total_rows + 1)
        for number in range(1, instance.seats_per_row + 1)
    ]
    SessionSeat.objects.bulk_create(seats, batch_size=1000)
