# n-feed

[![CI](https://github.com/naevor/n-feed/actions/workflows/ci.yml/badge.svg)](https://github.com/naevor/n-feed/actions/workflows/ci.yml)

n-feed is a Django Twitter-style backend project with server-rendered pages, a versioned REST API, JWT auth, hashtags, notifications, tests, CI, and Docker-ready production settings.

## Stack

- Django 5.2
- Django REST Framework
- Simple JWT
- drf-spectacular OpenAPI docs
- PostgreSQL or SQLite
- Redis cache
- pytest, ruff, pre-commit
- Docker Compose with PostgreSQL, Redis, Gunicorn, Nginx

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
- `GET /api/docs/`
- `GET /api/redoc/`
- `GET /api/v1/tweets/`
- `GET /api/v1/tags/trending/`

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pre-commit.exe run --all-files
```

## Settings

Settings are split by environment:

- `twitmain.settings.dev` for local development
- `twitmain.settings.prod` for container/production runtime
- `twitmain.settings` switches based on `DJANGO_ENV=dev|prod`

Production requires `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`. Docker Compose provides local-safe defaults and disables HTTPS-only cookie behavior so the app works over local HTTP.
