import asyncio
import os

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse

from .celery import app as celery_app


def healthz(request):
    return JsonResponse({"status": "ok"})


def readyz(request):
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "channels": _check_channels(),
    }
    is_ready = all(status == "ok" for status in checks.values())
    return JsonResponse(
        {
            "status": "ok" if is_ready else "error",
            "checks": checks,
        },
        status=200 if is_ready else 503,
    )


def celeryz(request):
    check = _check_celery()
    return JsonResponse(
        {
            "status": "ok" if check["status"] == "ok" else "error",
            "checks": {
                "celery": check,
            },
        },
        status=200 if check["status"] == "ok" else 503,
    )


def _check_database():
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return "error"
    return "ok"


def _check_channels():
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return "error"

    try:
        return async_to_sync(_channel_layer_roundtrip)(channel_layer)
    except Exception:
        return "error"


async def _channel_layer_roundtrip(channel_layer):
    channel_name = await channel_layer.new_channel("healthcheck")
    await channel_layer.send(channel_name, {"type": "healthcheck.ping"})
    message = await asyncio.wait_for(channel_layer.receive(channel_name), timeout=1)
    return "ok" if message.get("type") == "healthcheck.ping" else "error"


def _check_celery():
    if settings.CELERY_TASK_ALWAYS_EAGER:
        return {
            "status": "ok",
            "mode": "eager",
            "workers": 0,
        }

    timeout = float(os.environ.get("CELERY_HEALTHCHECK_TIMEOUT", "1"))
    try:
        responses = celery_app.control.ping(timeout=timeout)
    except Exception:
        return {
            "status": "error",
            "mode": "worker",
            "workers": 0,
        }

    return {
        "status": "ok" if responses else "error",
        "mode": "worker",
        "workers": len(responses),
    }


def _check_cache():
    cache_key = "healthcheck:readyz"
    try:
        cache.set(cache_key, "ok", timeout=5)
        if cache.get(cache_key) != "ok":
            return "error"
    except Exception:
        return "error"
    return "ok"
