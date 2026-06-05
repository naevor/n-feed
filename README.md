# n-feed

[![CI](https://github.com/naevor/n-feed/actions/workflows/ci.yml/badge.svg)](https://github.com/naevor/n-feed/actions/workflows/ci.yml)

n-feed is a Django Twitter-style backend project with server-rendered pages, a versioned REST API, JWT auth, hashtags, real-time notifications, tests, CI, and Docker-ready production settings.

## Stack

- Django 5.2
- Django REST Framework
- Simple JWT
- Channels and Daphne
- Celery and django-celery-beat
- drf-spectacular OpenAPI docs
- PostgreSQL or SQLite
- Redis cache
- pytest, ruff, pre-commit
- Docker Compose with PostgreSQL, Redis, Daphne, Celery, Nginx

## Architecture

```mermaid
flowchart LR
    Browser[Browser / API client] --> Nginx[Nginx]
    Nginx --> Web[Daphne + Django ASGI]
    Web --> Postgres[(PostgreSQL)]
    Web --> Redis[(Redis cache / channels / broker)]
    Web --> Media[(media volume)]
    Web --> OpenAPI[OpenAPI schema]
    Celery[Celery worker] --> Redis
    Celery --> Postgres
    Beat[Celery beat] --> Postgres
    Beat --> Redis
```

The Django app serves HTML pages, REST API endpoints, and websocket consumers from the same ASGI process. Shared business rules live in services and selectors, so templates, API viewsets, signals, and Celery tasks call the same project logic instead of duplicating mutations or feed queries.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

The local default uses SQLite. Set `DB_ENGINE=postgres` and the `POSTGRES_*` variables in `.env` to use PostgreSQL.

## Docker Quickstart

```powershell
docker compose --env-file .env.example up --build
```

Open `http://127.0.0.1:8000/`.

Using `.env.example` for Compose avoids accidental interpolation of special characters from a local Django `.env` secret.

Seed demo data:

```powershell
docker compose exec web python manage.py seed_demo --users=20 --tweets=200 --reset
```

Useful endpoints:

- `GET /healthz/`
- `GET /readyz/`
- `GET /celeryz/`
- `GET /api/docs/`
- `GET /api/redoc/`
- `GET /api/v1/tweets/`
- `GET /api/v1/tags/trending/`
- `WS /ws/notifications/`
- `WS /ws/feed/`

Docker Compose starts the web process, a Celery worker, and Celery beat. The web container runs migrations and creates the default periodic task that removes old notifications.

For local development without Redis, Celery tasks run eagerly by default through `CELERY_TASK_ALWAYS_EAGER=True`.
If you want to test the real queue locally, run Redis and set:

```powershell
$env:CELERY_TASK_ALWAYS_EAGER="False"
$env:CELERY_BROKER_URL="redis://localhost:6379/0"
celery -A twitmain worker -l info
celery -A twitmain beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Production Notes

Use `DJANGO_ENV=prod`, PostgreSQL, Redis, and a real reverse proxy with HTTPS. Start the web process with Daphne because the project uses websocket consumers.

Required production steps:

1. Set all variables from `.env.production.example`.
2. Run `python manage.py migrate --noinput`.
3. Run `python manage.py collectstatic --noinput`.
4. Run `python manage.py configure_periodic_tasks`.
5. Start Daphne, one Celery worker, and Celery beat.
6. Point the load balancer health check at `/readyz/`.

`/healthz/` only confirms that Django can return a response. `/readyz/` checks the database, cache, and Channels layer, so it is the endpoint to use before sending traffic to a web container. `/celeryz/` checks Celery worker visibility separately; it is intentionally not part of web readiness to avoid startup dependency cycles.

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pre-commit.exe run --all-files
.\.venv\Scripts\python.exe manage.py collectstatic --dry-run --noinput --verbosity 0
```

## Settings

Settings are split by environment:

- `twitmain.settings.dev` for local development
- `twitmain.settings.prod` for container/production runtime
- `twitmain.settings` switches based on `DJANGO_ENV=dev|prod`

Production requires `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`. Docker Compose provides local-safe defaults and disables HTTPS-only cookie behavior so the app works over local HTTP.
