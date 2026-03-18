import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Movie, Session


class Command(BaseCommand):
    help = 'Seed sample movies and sessions (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--if-empty',
            action='store_true',
            help='Only seed when there are no movies.',
        )

    def handle(self, *args, **options):
        if options.get('if_empty') and Movie.objects.exists():
            self.stdout.write(self.style.WARNING('Movies already exist. Skipping seed.'))
            return

        sample_movies = [
            {
                'title': 'Noite de Neblina',
                'description': 'Um suspense noir pelas ruas de Natal.',
                'duration_minutes': 112,
            },
            {
                'title': 'Estrela do Atlantico',
                'description': 'Drama familiar com grandes paisagens litoraneas.',
                'duration_minutes': 124,
            },
            {
                'title': 'Mapa das Mares',
                'description': 'Aventura de resgate em alto mar.',
                'duration_minutes': 98,
            },
            {
                'title': 'Cafe das Seis',
                'description': 'Romance leve em uma cafeteria historica.',
                'duration_minutes': 105,
            },
            {
                'title': 'Circuito Solar',
                'description': 'Sci-fi otimista sobre energia limpa.',
                'duration_minutes': 118,
            },
            {
                'title': 'Ultimo Voo para Recife',
                'description': 'Misterio de aeroporto com reviravoltas.',
                'duration_minutes': 110,
            },
        ]

        now = timezone.now()
        created = 0
        for idx, payload in enumerate(sample_movies):
            movie = Movie.objects.create(
                title=payload['title'],
                description=payload['description'],
                duration_minutes=payload['duration_minutes'],
                rating=str(random.randint(1, 5)),
            )
            created += 1
            for offset in (1, 2, 4):
                Session.objects.create(
                    movie=movie,
                    starts_at=now + timezone.timedelta(days=offset + idx),
                    auditorium=f'Sala {(idx % 3) + 1}',
                    total_rows=8,
                    seats_per_row=12,
                )

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} movies with sessions.'))
