from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Movie, Session, SessionSeat, Ticket

User = get_user_model()


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
