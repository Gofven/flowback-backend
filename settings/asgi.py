import os

from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from .middleware import TokenAuthMiddleware

from flowback.chat import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
        'websocket': AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter(
                    routing.websockets_urlpatterns
                )
            )
        )
    })
