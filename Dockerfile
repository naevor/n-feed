FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_ENV=prod \
    DJANGO_SECRET_KEY=build-time-secret \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    DJANGO_SECURE_SSL_REDIRECT=False \
    DJANGO_COOKIE_SECURE=False \
    DB_ENGINE=sqlite

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY --chown=app:app . .

USER app
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "twitmain.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
