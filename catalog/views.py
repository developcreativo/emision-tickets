from rest_framework import permissions, viewsets

from .models import DrawSchedule, DrawType, NumberLimit, Zone
from .serializers import (
    DrawScheduleSerializer,
    DrawTypeSerializer,
    NumberLimitSerializer,
    ZoneSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'ADMIN')


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('name')
    serializer_class = ZoneSerializer
    permission_classes = [IsAdminOrReadOnly]


class DrawTypeViewSet(viewsets.ModelViewSet):
    queryset = DrawType.objects.all().order_by('name')
    serializer_class = DrawTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class DrawScheduleViewSet(viewsets.ModelViewSet):
    queryset = DrawSchedule.objects.select_related('draw_type', 'zone').all()
    serializer_class = DrawScheduleSerializer
    permission_classes = [IsAdminOrReadOnly]


class NumberLimitViewSet(viewsets.ModelViewSet):
    queryset = NumberLimit.objects.select_related('draw_type', 'zone').all()
    serializer_class = NumberLimitSerializer
    permission_classes = [IsAdminOrReadOnly]



