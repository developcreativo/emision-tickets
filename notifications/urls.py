from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para API REST
router = DefaultRouter()
router.register(
    r'notifications', views.NotificationViewSet, basename='notification'
)
router.register(
    r'templates', views.NotificationTemplateViewSet, basename='template'
)
router.register(
    r'preferences', views.NotificationPreferenceViewSet, basename='preference'
)
router.register(
    r'service', views.NotificationServiceViewSet, basename='service'
)

# URLs de la API
api_urlpatterns = [
    path('', include(router.urls)),
]

# URLs de WebSocket (se incluyen en routing.py)
websocket_urlpatterns = [
    # Estas URLs se definen en routing.py
]
