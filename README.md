# Cinepolis Natal API

API de ingressos para o cinema Cinépolis Natal.

## Requisitos
- Docker e Docker Compose (recomendado)
- Python 3.12 + Poetry (para execução local)

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

## Variáveis de ambiente
Use `.env.example` como base.

Principais:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_*`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CORS_ALLOW_ALL_ORIGINS`
- `CORS_ALLOWED_ORIGINS`

## Recursos implementados
- Autenticação JWT (SimpleJWT)
- PostgreSQL
- Redis para cache e locks de assentos
- Celery (worker + beat) para tarefas assíncronas
- Paginação obrigatória em listagens
- Rate limiting (DRF throttling)
- Documentação Swagger/Redoc

### Cache
- `GET /api/movies/` e `GET /api/movies/{id}/sessions/` usam cache Redis (TTL 300s).

### Locks de assentos
- Reserva com lock temporário (TTL 10 minutos).
- Celery Beat limpa locks expirados a cada 60s.

## Testes
```bash
poetry run python manage.py test
```

Observações:
- Alguns testes dependem do Redis e são ignorados se o Redis não estiver disponível.
- Para rodar tudo localmente, use `docker compose up` e execute os testes no container `web`.

Exemplo usando Docker:
```bash
docker compose exec web poetry run python manage.py test
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

## Frontend básico
Frontend servido pelo próprio backend. Acesse:
`https://desafiobackend2026-production.up.railway.app`
Se quiser testar localmente, ainda pode abrir `frontend/index.html`.

## Testes rápidos (frontend)
1. Abra o frontend (Railway ou `frontend/index.html`).
2. Clique **Limpar** na seção de Configuracao.
3. Base URL: `https://desafiobackend2026-production.up.railway.app` (sem barra no final).
4. Clique **Salvar** e depois **Testar conexao**.
5. Cadastre um usuario e faça login.
6. Clique **Carregar filmes** e escolha um filme.
7. Selecione uma sessao, escolha um assento disponivel, **Reservar** e **Checkout**.
8. Clique **Carregar ingressos** em Meus ingressos.

## Seed automatico
No startup, o app executa:
- `python manage.py migrate --noinput`
- `python manage.py seed_movies --if-empty --ensure-seats`

Isso cria filmes, sessoes e assentos apenas quando o banco esta vazio. Se o banco ja tiver dados, o comando apenas garante assentos para sessoes sem assentos.

## Testes rápidos (curl)
```bash
# cadastro
curl -X POST https://desafiobackend2026-production.up.railway.app/api/auth/register/ \\
  -H "Content-Type: application/json" \\
  -d '{"email":"teste@exemplo.com","username":"user1","password":"senha123"}'

# login (JWT)
curl -X POST https://desafiobackend2026-production.up.railway.app/api/auth/token/ \\
  -H "Content-Type: application/json" \\
  -d '{"username":"user1","password":"senha123"}'
```

## Base URL (produção)
`https://desafiobackend2026-production.up.railway.app`

## Endpoints completos (produção)
- `POST https://desafiobackend2026-production.up.railway.app/api/auth/register/`
- `POST https://desafiobackend2026-production.up.railway.app/api/auth/token/`
- `POST https://desafiobackend2026-production.up.railway.app/api/auth/token/refresh/`
- `GET https://desafiobackend2026-production.up.railway.app/api/movies/`
- `GET https://desafiobackend2026-production.up.railway.app/api/movies/{movie_id}/sessions/`
- `GET https://desafiobackend2026-production.up.railway.app/api/sessions/{session_id}/seats/`
- `POST https://desafiobackend2026-production.up.railway.app/api/sessions/{session_id}/reserve/`
- `POST https://desafiobackend2026-production.up.railway.app/api/sessions/{session_id}/checkout/`
- `GET https://desafiobackend2026-production.up.railway.app/api/me/tickets/`
- `GET https://desafiobackend2026-production.up.railway.app/api/docs/`
- `GET https://desafiobackend2026-production.up.railway.app/api/redoc/`
