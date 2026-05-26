from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse


def healthz(request):
    return JsonResponse({"status": "ok"})


def readyz(request):
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
    }
    is_ready = all(status == "ok" for status in checks.values())
    return JsonResponse(
        {
            "status": "ok" if is_ready else "error",
            "checks": checks,
        },
        status=200 if is_ready else 503,
    )


def _check_database():
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return "error"
    return "ok"


def _check_cache():
    cache_key = "healthcheck:readyz"
    try:
        cache.set(cache_key, "ok", timeout=5)
        if cache.get(cache_key) != "ok":
            return "error"
    except Exception:
        return "error"
    return "ok"
