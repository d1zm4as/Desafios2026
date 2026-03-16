from django.contrib import admin

from core.models import Movie, Session, SessionSeat, Ticket

admin.site.register(Movie)
admin.site.register(Session)
admin.site.register(SessionSeat)
admin.site.register(Ticket)

# Register your models here.
