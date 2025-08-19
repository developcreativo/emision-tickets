from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from catalog.models import DrawSchedule, NumberLimit

from .models import Ticket, TicketItem


class TicketItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketItem
        fields = ('number', 'pieces')


class TicketSerializer(serializers.ModelSerializer):
    items = TicketItemSerializer(many=True)

    class Meta:
        model = Ticket
        fields = ('id', 'created_at', 'zone', 'draw_type', 'user', 'total_pieces', 'items')
        read_only_fields = ('id', 'created_at', 'user', 'total_pieces')

    def validate(self, data):
        zone = data['zone']
        draw_type = data['draw_type']
        items_data = self.initial_data.get('items', [])

        now = timezone.localtime().time()
        try:
            schedule = DrawSchedule.objects.get(zone=zone, draw_type=draw_type, is_active=True)
        except DrawSchedule.DoesNotExist:
            raise serializers.ValidationError('No hay horario configurado para esta zona y sorteo.')
        if now >= schedule.cutoff_time:
            raise serializers.ValidationError('Cerrado para este sorteo según el horario configurado.')

        limits = {l.number: l.max_pieces for l in NumberLimit.objects.filter(zone=zone, draw_type=draw_type)}
        # Validación de entrada básica y topes acumulados diarios por zona+sorteo+número
        today = timezone.localdate()
        for item in items_data:
            number = item.get('number')
            pieces = int(item.get('pieces', 0))
            if not number or len(number) != 2 or not number.isdigit():
                raise serializers.ValidationError('Número inválido, debe ser 00-99.')
            max_allowed = limits.get(number, None)
            if max_allowed is not None:
                sold = (
                    TicketItem.objects
                    .filter(
                        ticket__zone=zone,
                        ticket__draw_type=draw_type,
                        ticket__created_at__date=today,
                        number=number,
                    )
                    .aggregate(total=Sum('pieces'))
                    .get('total') or 0
                )
                if sold + pieces > max_allowed:
                    raise serializers.ValidationError(
                        f'Tope acumulado excedido para el número {number}: {sold}+{pieces} > {max_allowed}.'
                    )
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        ticket = Ticket.objects.create(**validated_data)
        total = 0
        for item in items_data:
            obj = TicketItem.objects.create(ticket=ticket, **item)
            total += obj.pieces
        ticket.total_pieces = total
        ticket.save(update_fields=['total_pieces'])
        return ticket


