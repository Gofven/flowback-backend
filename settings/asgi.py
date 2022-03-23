import os

from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from .middleware import TokenAuthMiddleware

from flowback.chat import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')

application = ProtocolTypeRouter({
        'websocket': AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter(
                    routing.websockets_urlpatterns
                )
            )
        )
    })
