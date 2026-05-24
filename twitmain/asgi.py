"""
ASGI config for twitmain project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twitmain.settings")

django_asgi_app = get_asgi_application()

from notifications import routing as notification_routing  # noqa: E402
from tweets import routing as tweet_routing  # noqa: E402

websocket_urlpatterns = [
    *notification_routing.websocket_urlpatterns,
    *tweet_routing.websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
