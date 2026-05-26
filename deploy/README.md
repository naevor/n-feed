# Deployment

This directory contains deployment-facing examples. They are intentionally generic, so copy them into your hosting provider configuration instead of treating them as one-click production manifests.

## Runtime Processes

Run these long-lived processes:

- `daphne -b 0.0.0.0 -p 8000 twitmain.asgi:application`
- `celery -A twitmain worker -l info`
- `celery -A twitmain beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

Run these release commands before the new web process receives traffic:

```powershell
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py configure_periodic_tasks
```

## Health Checks

Use `/readyz/` for container readiness checks. It verifies:

- database connection
- configured Django cache backend

Use `/healthz/` only as a lightweight process liveness check.

## Required Services

- PostgreSQL
- Redis
- persistent media storage or a mounted media volume
- HTTPS reverse proxy with websocket upgrade headers

`nginx.conf` shows the required websocket forwarding headers for `/ws/`.
