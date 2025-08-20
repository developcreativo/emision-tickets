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
        # Permitir escritura a superusuarios, staff o usuarios con rol ADMIN
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
        return getattr(user, "role", None) == "ADMIN"


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by("name")
    serializer_class = ZoneSerializer
    permission_classes = [IsAdminOrReadOnly]


class DrawTypeViewSet(viewsets.ModelViewSet):
    queryset = DrawType.objects.all().order_by("name")
    serializer_class = DrawTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class DrawScheduleViewSet(viewsets.ModelViewSet):
    queryset = DrawSchedule.objects.select_related("draw_type", "zone").all()
    serializer_class = DrawScheduleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def create(self, request, *args, **kwargs):
        """Upsert por (zone, draw_type): si existe, actualiza; si no, crea."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        zone = validated["zone"]
        draw_type = validated["draw_type"]
        cutoff_time = validated.get("cutoff_time")
        is_active = validated.get("is_active", True)

        instance, created = DrawSchedule.objects.get_or_create(
            zone=zone,
            draw_type=draw_type,
            defaults={"cutoff_time": cutoff_time, "is_active": is_active},
        )
        if not created:
            if cutoff_time is not None:
                instance.cutoff_time = cutoff_time
            instance.is_active = is_active
            instance.save()

        output = self.get_serializer(instance)
        from rest_framework import status as drf_status
        from rest_framework.response import Response

        return Response(output.data, status=drf_status.HTTP_201_CREATED)


class NumberLimitViewSet(viewsets.ModelViewSet):
    queryset = NumberLimit.objects.select_related("draw_type", "zone").all()
    serializer_class = NumberLimitSerializer
    permission_classes = [IsAdminOrReadOnly]
