"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import chat.routing
from .middleware import JwtAuthMiddlewareStack
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

# from channels.security.websocket import AllowedHostsOriginValidator
# from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JwtAuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    )
})
