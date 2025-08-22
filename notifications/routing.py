from django.urls import re_path
from . import consumers

# URLs de WebSocket
websocket_urlpatterns = [
    # Notificaciones por usuario (con token)
    re_path(
        r'ws/notifications/(?P<token>[^/]+)/$',
        consumers.NotificationConsumer.as_asgi()
    ),
    
    # Notificaciones por usuario (sin token, usa sesión)
    re_path(
        r'ws/notifications/$',
        consumers.NotificationConsumer.as_asgi()
    ),
    
    # Broadcast para administradores
    re_path(
        r'ws/broadcast/$',
        consumers.BroadcastConsumer.as_asgi()
    ),
]
