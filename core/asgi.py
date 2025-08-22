"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Aplicación ASGI principal
application = ProtocolTypeRouter({
    # HTTP requests -> Django views
    "http": get_asgi_application(),
    
    # WebSocket requests -> Channels consumers
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})



