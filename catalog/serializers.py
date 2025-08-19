from rest_framework import serializers

from .models import DrawSchedule, DrawType, NumberLimit, Zone


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ('id', 'name', 'is_active')


class DrawTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawType
        fields = ('id', 'code', 'name', 'is_active')


class DrawScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawSchedule
        fields = ('id', 'draw_type', 'zone', 'cutoff_time', 'is_active')


class NumberLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberLimit
        fields = ('id', 'draw_type', 'zone', 'number', 'max_pieces')



