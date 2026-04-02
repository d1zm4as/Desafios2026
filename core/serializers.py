from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Movie, Session, SessionSeat, Ticket


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )

    def validate_email(self, value: str) -> str:
        email = value.strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Email already registered.')
        return email


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'duration_minutes', 'rating')


class SessionSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Session
        fields = ('id', 'movie', 'starts_at', 'auditorium', 'total_rows', 'seats_per_row')


class SessionSeatSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)

    class Meta:
        model = SessionSeat
        fields = ('id', 'row', 'number', 'status')


class TicketSerializer(serializers.ModelSerializer):
    session = serializers.SerializerMethodField()
    seat = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ('id', 'code', 'purchased_at', 'session', 'seat')

    def get_session(self, obj: Ticket):
        session = obj.session_seat.session
        return {
            'id': session.id,
            'movie_title': session.movie.title,
            'starts_at': session.starts_at,
            'auditorium': session.auditorium,
        }

    def get_seat(self, obj: Ticket):
        seat = obj.session_seat
        return {'row': seat.row, 'number': seat.number}


class SeatActionSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField(min_value=1)
