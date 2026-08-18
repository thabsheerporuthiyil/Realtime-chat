"""
ASGI configuration for the Real-Time Chat API project.

Routes HTTP traffic to Django and WebSocket traffic to
the Channels consumer layer with JWT authentication.
"""
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialize Django ASGI application early to populate AppRegistry
# before importing consumers or middleware that depend on models.
django_asgi_app = get_asgi_application()

# These imports must come AFTER get_asgi_application() to ensure
# the Django app registry is fully populated.
from apps.chat.middleware import JWTAuthMiddleware  # noqa: E402
from apps.chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
