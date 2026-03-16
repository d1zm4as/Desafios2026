from django.core.cache import cache
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.locks import (
    acquire_lock,
    get_session_locks,
    is_locked_by_other,
    is_locked_by_user,
    release_lock,
)
from core.models import Movie, Session, SessionSeat, Ticket
from core.serializers import (
    MovieSerializer,
    RegisterSerializer,
    SeatActionSerializer,
    SessionSerializer,
    TicketSerializer,
)
from core.tasks import send_ticket_confirmation_email


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MovieListView(generics.ListAPIView):
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Movie.objects.filter(is_active=True).order_by('title')

    def list(self, request, *args, **kwargs):
        cache_key = f'movies:list:{request.get_full_path()}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response


class SessionListView(generics.ListAPIView):
    serializer_class = SessionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Session.objects.filter(movie_id=self.kwargs['movie_id'])

    def list(self, request, *args, **kwargs):
        cache_key = f'sessions:list:{self.kwargs["movie_id"]}:{request.get_full_path()}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response


class SessionSeatMapView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, session_id: int):
        session = generics.get_object_or_404(Session, pk=session_id)
        seats = SessionSeat.objects.filter(session=session)
        purchased_ids = set(
            Ticket.objects.filter(session_seat__session=session).values_list('session_seat_id', flat=True)
        )
        locks = get_session_locks(session.id)

        payload = []
        for seat in seats:
            if seat.id in purchased_ids:
                status_label = 'purchased'
            elif seat.id in locks:
                status_label = 'reserved'
            else:
                status_label = 'available'
            payload.append(
                {
                    'id': seat.id,
                    'row': seat.row,
                    'number': seat.number,
                    'status': status_label,
                }
            )
        return Response(payload)


class ReserveSeatView(APIView):
    def post(self, request, session_id: int):
        serializer = SeatActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seat_id = serializer.validated_data['seat_id']
        seat = generics.get_object_or_404(SessionSeat, pk=seat_id, session_id=session_id)

        if Ticket.objects.filter(session_seat=seat).exists():
            return Response({'detail': 'Seat already purchased.'}, status=status.HTTP_409_CONFLICT)

        if is_locked_by_other(request.user.id, session_id, seat.id):
            return Response({'detail': 'Seat is already reserved.'}, status=status.HTTP_409_CONFLICT)

        if not acquire_lock(request.user.id, session_id, seat.id):
            return Response({'detail': 'Unable to reserve seat.'}, status=status.HTTP_409_CONFLICT)

        return Response({'detail': 'Seat reserved.'}, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    def post(self, request, session_id: int):
        serializer = SeatActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seat_id = serializer.validated_data['seat_id']

        seat = generics.get_object_or_404(SessionSeat, pk=seat_id, session_id=session_id)

        if Ticket.objects.filter(session_seat=seat).exists():
            return Response({'detail': 'Seat already purchased.'}, status=status.HTTP_409_CONFLICT)

        if is_locked_by_other(request.user.id, session_id, seat.id):
            return Response({'detail': 'Seat is reserved by another user.'}, status=status.HTTP_409_CONFLICT)

        if not is_locked_by_user(request.user.id, session_id, seat.id):
            return Response({'detail': 'Seat is not reserved.'}, status=status.HTTP_409_CONFLICT)

        ticket = Ticket.objects.create(user=request.user, session_seat=seat)
        release_lock(request.user.id, session_id, seat.id)
        send_ticket_confirmation_email.delay(request.user.id, str(ticket.code))
        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyTicketsView(generics.ListAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        status_param = self.request.query_params.get('status', 'all')
        queryset = Ticket.objects.filter(user=self.request.user).select_related('session_seat__session__movie')

        now = timezone.now()
        if status_param == 'upcoming':
            queryset = queryset.filter(session_seat__session__starts_at__gte=now)
        elif status_param == 'past':
            queryset = queryset.filter(session_seat__session__starts_at__lt=now)
        return queryset
