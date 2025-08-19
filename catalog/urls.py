from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DrawScheduleViewSet, DrawTypeViewSet, NumberLimitViewSet, ZoneViewSet

router = DefaultRouter()
router.register(r'zones', ZoneViewSet)
router.register(r'draw-types', DrawTypeViewSet)
router.register(r'draw-schedules', DrawScheduleViewSet)
router.register(r'number-limits', NumberLimitViewSet)

urlpatterns = [
    path('', include(router.urls)),
]



