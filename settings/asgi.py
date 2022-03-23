import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django_asgi_app = get_asgi_application()

from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from .middleware import TokenAuthMiddleware
from flowback.chat import routing


application = ProtocolTypeRouter({
        'websocket': AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter(
                    routing.websockets_urlpatterns
                )
            )
        )
    })
