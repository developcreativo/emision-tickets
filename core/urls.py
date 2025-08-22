from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Health check endpoint (debe ir antes de las APIs)
    path("api/health/", health_check, name="health_check"),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/", 
        SpectacularSwaggerView.as_view(url_name="schema"), 
        name="swagger-ui"
    ),
    path(
        "api/redoc/", 
        SpectacularRedocView.as_view(url_name="schema"), 
        name="redoc"
    ),
    
    # APIs de la aplicación
    path("api/", include("routes.api")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, 
        document_root=settings.STATIC_ROOT
    )
