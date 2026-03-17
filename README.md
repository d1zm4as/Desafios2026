# Cinepolis Natal API

API de ingressos para o cinema Cinépolis Natal.

## Requisitos
- Docker e Docker Compose

## Subir o projeto
```bash
docker compose up --build
```

## Execução local (sem Docker)
```bash
poetry install --no-root
poetry run python manage.py migrate --noinput
poetry run gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Checklist rápido (smoke test)
```bash
# 1) cadastro
curl -X POST http://localhost:8000/api/auth/register/ \\
  -H "Content-Type: application/json" \\
  -d '{"email":"teste@exemplo.com","username":"user1","password":"senha123"}'

# 2) login (JWT)
curl -X POST http://localhost:8000/api/auth/token/ \\
  -H "Content-Type: application/json" \\
  -d '{"username":"user1","password":"senha123"}'

# 3) listar filmes
curl http://localhost:8000/api/movies/
```

## Endpoints principais
- `POST /api/auth/register/` cadastro
- `POST /api/auth/token/` login (JWT)
- `GET /api/movies/` lista de filmes (paginado)
- `GET /api/movies/{movie_id}/sessions/` sessões por filme (paginado)
- `GET /api/sessions/{session_id}/seats/` mapa de assentos
- `POST /api/sessions/{session_id}/reserve/` reservar assento
- `POST /api/sessions/{session_id}/checkout/` finalizar compra
- `GET /api/me/tickets/` meus ingressos (paginado)

## Documentação
- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`

## Base URL (produção)
`https://desafiobackend-production.up.railway.app`

## Endpoints completos (produção)
- `POST https://desafiobackend-production.up.railway.app/api/auth/register/`
- `POST https://desafiobackend-production.up.railway.app/api/auth/token/`
- `POST https://desafiobackend-production.up.railway.app/api/auth/token/refresh/`
- `GET https://desafiobackend-production.up.railway.app/api/movies/`
- `GET https://desafiobackend-production.up.railway.app/api/movies/{movie_id}/sessions/`
- `GET https://desafiobackend-production.up.railway.app/api/sessions/{session_id}/seats/`
- `POST https://desafiobackend-production.up.railway.app/api/sessions/{session_id}/reserve/`
- `POST https://desafiobackend-production.up.railway.app/api/sessions/{session_id}/checkout/`
- `GET https://desafiobackend-production.up.railway.app/api/me/tickets/`
- `GET https://desafiobackend-production.up.railway.app/api/docs/`
- `GET https://desafiobackend-production.up.railway.app/api/redoc/`
