# Cinepolis Natal API

API de ingressos para o cinema Cinépolis Natal.

## Requisitos
- Docker e Docker Compose

## Subir o projeto
```bash
docker compose up --build
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
