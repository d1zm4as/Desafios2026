import unittest

import redis
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Movie, Session, SessionSeat, Ticket
from core.locks import LOCK_INDEX_KEY, LOCK_KEY_PREFIX
from core.tasks import cleanup_expired_locks

User = get_user_model()

def _redis_available() -> bool:
    try:
        return redis.Redis.from_url(settings.REDIS_URL).ping()
    except Exception:
        return False


def _auth_client(username: str, email: str, password: str) -> APIClient:
    client = APIClient()
    User.objects.create_user(email=email, username=username, password=password)
    token_response = client.post(
        '/api/auth/token/', {'username': username, 'password': password}, format='json'
    )
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_response.data["access"]}')
    return client


class AuthTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_register_and_login(self):
        payload = {'email': 'user@example.com', 'username': 'user1', 'password': 'testpass123'}
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, 201)

        token_response = self.client.post(
            '/api/auth/token/', {'username': 'user1', 'password': 'testpass123'}, format='json'
        )
        self.assertEqual(token_response.status_code, 200)
        self.assertIn('access', token_response.data)

    def test_register_rejects_duplicate_email(self):
        first = {'email': 'user@example.com', 'username': 'user1', 'password': 'testpass123'}
        second = {'email': 'USER@example.com', 'username': 'user2', 'password': 'testpass123'}
        response_1 = self.client.post('/api/auth/register/', first, format='json')
        self.assertEqual(response_1.status_code, 201)

        response_2 = self.client.post('/api/auth/register/', second, format='json')
        self.assertEqual(response_2.status_code, 400)
        self.assertIn('email', response_2.data)


class TicketFlowTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(email='buyer@example.com', username='buyer', password='pass12345')
        token_response = self.client.post(
            '/api/auth/token/', {'username': 'buyer', 'password': 'pass12345'}, format='json'
        )
        self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.movie = Movie.objects.create(
            title='Movie 1', description='Test', duration_minutes=120, rating='PG'
        )
        self.session = Session.objects.create(
            movie=self.movie, starts_at=timezone.now() + timezone.timedelta(days=1), auditorium='Room A'
        )
        self.seat = SessionSeat.objects.filter(session=self.session).first()

    def test_reserve_checkout_and_list_tickets(self):
        reserve_response = self.client.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat.id}, format='json'
        )
        self.assertEqual(reserve_response.status_code, 200)

        checkout_response = self.client.post(
            f'/api/sessions/{self.session.id}/checkout/', {'seat_id': self.seat.id}, format='json'
        )
        self.assertEqual(checkout_response.status_code, 201)

        self.assertTrue(Ticket.objects.filter(session_seat=self.seat).exists())

        tickets_response = self.client.get('/api/me/tickets/')
        self.assertEqual(tickets_response.status_code, 200)
        self.assertEqual(len(tickets_response.data['results']), 1)


class AuthRequiredTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.movie = Movie.objects.create(
            title='Movie', description='Test', duration_minutes=90, rating='PG'
        )
        self.session = Session.objects.create(
            movie=self.movie,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            auditorium='Room A',
            total_rows=1,
            seats_per_row=2,
        )
        self.seat = SessionSeat.objects.filter(session=self.session).first()

    def test_reserve_requires_auth(self):
        response = self.client.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat.id}, format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_checkout_requires_auth(self):
        response = self.client.post(
            f'/api/sessions/{self.session.id}/checkout/', {'seat_id': self.seat.id}, format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_my_tickets_requires_auth(self):
        response = self.client.get('/api/me/tickets/')
        self.assertEqual(response.status_code, 401)


class PaginationTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_movies_are_paginated(self):
        Movie.objects.bulk_create(
            [
                Movie(
                    title=f'Movie {i}',
                    description='Test',
                    duration_minutes=100,
                    rating='PG',
                    is_active=True,
                )
                for i in range(25)
            ]
        )
        response = self.client.get('/api/movies/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])

    def test_sessions_are_paginated(self):
        movie = Movie.objects.create(
            title='Movie', description='Test', duration_minutes=100, rating='PG'
        )
        for i in range(25):
            Session.objects.create(
                movie=movie,
                starts_at=timezone.now() + timezone.timedelta(days=i),
                auditorium='Room A',
                total_rows=1,
                seats_per_row=1,
            )
        response = self.client.get(f'/api/movies/{movie.id}/sessions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])

    def test_sessions_movie_not_found_returns_404(self):
        response = self.client.get('/api/movies/999/sessions/')
        self.assertEqual(response.status_code, 404)

    def test_my_tickets_are_paginated(self):
        client = _auth_client('buyer', 'buyer@example.com', 'pass12345')
        user = User.objects.get(username='buyer')
        movie = Movie.objects.create(
            title='Movie', description='Test', duration_minutes=100, rating='PG'
        )
        session = Session.objects.create(
            movie=movie,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            auditorium='Room A',
            total_rows=1,
            seats_per_row=25,
        )
        seats = list(SessionSeat.objects.filter(session=session)[:21])
        Ticket.objects.bulk_create([Ticket(user=user, session_seat=seat) for seat in seats])

        response = client.get('/api/me/tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 21)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])


@unittest.skipUnless(_redis_available(), 'Redis not available')
class SeatLockingEdgeCaseTests(TestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            email='user1@example.com', username='user1', password='pass12345'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com', username='user2', password='pass12345'
        )
        self.client1 = APIClient()
        self.client2 = APIClient()
        token1 = self.client1.post(
            '/api/auth/token/', {'username': 'user1', 'password': 'pass12345'}, format='json'
        ).data['access']
        token2 = self.client2.post(
            '/api/auth/token/', {'username': 'user2', 'password': 'pass12345'}, format='json'
        ).data['access']
        self.client1.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        self.client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')

        self.movie = Movie.objects.create(
            title='Movie', description='Test', duration_minutes=120, rating='PG'
        )
        self.session = Session.objects.create(
            movie=self.movie,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            auditorium='Room A',
            total_rows=1,
            seats_per_row=3,
        )
        seats = list(SessionSeat.objects.filter(session=self.session))
        self.seat_a = seats[0]
        self.seat_b = seats[1]
        self.seat_c = seats[2]

    def test_reserve_conflict_between_users(self):
        reserve_1 = self.client1.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat_a.id}, format='json'
        )
        self.assertEqual(reserve_1.status_code, 200)

        reserve_2 = self.client2.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat_a.id}, format='json'
        )
        self.assertEqual(reserve_2.status_code, 409)

    def test_checkout_requires_existing_lock(self):
        response = self.client1.post(
            f'/api/sessions/{self.session.id}/checkout/', {'seat_id': self.seat_b.id}, format='json'
        )
        self.assertEqual(response.status_code, 409)

    def test_checkout_blocked_by_other_user_lock(self):
        reserve_1 = self.client1.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat_b.id}, format='json'
        )
        self.assertEqual(reserve_1.status_code, 200)
        checkout_2 = self.client2.post(
            f'/api/sessions/{self.session.id}/checkout/', {'seat_id': self.seat_b.id}, format='json'
        )
        self.assertEqual(checkout_2.status_code, 409)

    def test_seat_map_statuses(self):
        self.client1.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': self.seat_a.id}, format='json'
        )
        Ticket.objects.create(user=self.user1, session_seat=self.seat_b)

        response = self.client1.get(f'/api/sessions/{self.session.id}/seats/')
        self.assertEqual(response.status_code, 200)

        status_map = {seat['id']: seat['status'] for seat in response.data}
        self.assertEqual(status_map[self.seat_a.id], 'reserved')
        self.assertEqual(status_map[self.seat_b.id], 'purchased')
        self.assertEqual(status_map[self.seat_c.id], 'available')

    def test_invalid_seat_returns_404(self):
        other_session = Session.objects.create(
            movie=self.movie,
            starts_at=timezone.now() + timezone.timedelta(days=2),
            auditorium='Room B',
            total_rows=1,
            seats_per_row=1,
        )
        other_seat = SessionSeat.objects.filter(session=other_session).first()
        response = self.client1.post(
            f'/api/sessions/{self.session.id}/reserve/', {'seat_id': other_seat.id}, format='json'
        )
        self.assertEqual(response.status_code, 404)


@unittest.skipUnless(_redis_available(), 'Redis not available')
class CacheBehaviorTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_movie_list_cache_stale_after_new_movie(self):
        Movie.objects.create(title='Movie A', description='Test', duration_minutes=100, rating='PG')
        Movie.objects.create(title='Movie B', description='Test', duration_minutes=90, rating='PG')

        first = self.client.get('/api/movies/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['count'], 2)

        Movie.objects.create(title='Movie C', description='Test', duration_minutes=80, rating='PG')
        second = self.client.get('/api/movies/')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data['count'], 2)

    def test_session_list_cache_stale_after_new_session(self):
        movie = Movie.objects.create(title='Movie', description='Test', duration_minutes=100, rating='PG')
        Session.objects.create(
            movie=movie,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            auditorium='Room A',
            total_rows=1,
            seats_per_row=1,
        )
        first = self.client.get(f'/api/movies/{movie.id}/sessions/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['count'], 1)

        Session.objects.create(
            movie=movie,
            starts_at=timezone.now() + timezone.timedelta(days=2),
            auditorium='Room B',
            total_rows=1,
            seats_per_row=1,
        )
        second = self.client.get(f'/api/movies/{movie.id}/sessions/')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data['count'], 1)


@unittest.skipUnless(_redis_available(), 'Redis not available')
class LockCleanupTests(TestCase):
    def setUp(self) -> None:
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)

    def tearDown(self) -> None:
        pattern = f'{LOCK_KEY_PREFIX}:*'
        for key in self.redis_client.scan_iter(match=pattern, count=1000):
            self.redis_client.delete(key)
        self.redis_client.delete(LOCK_INDEX_KEY)

    def test_cleanup_expired_locks_removes_keys(self):
        key = f'{LOCK_KEY_PREFIX}:999:888'
        self.redis_client.set(key, '1:0', ex=600)
        self.redis_client.zadd(LOCK_INDEX_KEY, {key: int(timezone.now().timestamp()) - 60})

        self.assertTrue(self.redis_client.exists(key))
        deleted = cleanup_expired_locks()
        self.assertGreaterEqual(deleted, 1)
        self.assertFalse(self.redis_client.exists(key))


@unittest.skipUnless(_redis_available(), 'Redis not available')
@override_settings(
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ),
        'DEFAULT_THROTTLE_RATES': {
            'anon': '2/min',
            'user': '10/min',
        },
    }
)
class ThrottlingTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()
        self.client.defaults['REMOTE_ADDR'] = '10.0.0.99'
        Movie.objects.create(title='Movie A', description='Test', duration_minutes=100, rating='PG')

    def test_anon_throttle_limits_requests(self):
        first = self.client.get('/api/movies/')
        second = self.client.get('/api/movies/')
        third = self.client.get('/api/movies/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
