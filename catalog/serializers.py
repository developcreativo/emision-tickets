from rest_framework import serializers

from .models import DrawSchedule, DrawType, NumberLimit, Zone


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ("id", "name", "description", "is_active")
        validators = []


class DrawTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawType
        fields = ("id", "code", "name", "is_active")
        extra_kwargs = {
            "code": {"validators": []},
        }


class DrawScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawSchedule
        fields = ("id", "draw_type", "zone", "cutoff_time", "is_active")
        validators = []


class NumberLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberLimit
        fields = ("id", "draw_type", "zone", "number", "max_pieces")
        validators = []
