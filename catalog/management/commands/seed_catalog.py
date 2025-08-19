from datetime import time

from django.core.management.base import BaseCommand

from catalog.models import DrawSchedule, DrawType, Zone


class Command(BaseCommand):
    help = 'Carga datos base de zonas, tipos de sorteo y horarios'

    def handle(self, *args, **options):
        zones = ['Managua', 'León', 'Masaya']
        for z in zones:
            Zone.objects.get_or_create(name=z)

        draws = [
            ('santa', 'Santa'), ('bolido', 'Bólido'), ('charada', 'Charada'),
            ('duky', 'Duky'), ('diaria', 'Diaria'), ('nica', 'Nica'), ('salva', 'Salva'),
        ]
        for code, name in draws:
            DrawType.objects.get_or_create(code=code, defaults={'name': name})

        default_cutoff = time(hour=18, minute=0)
        for zone in Zone.objects.all():
            for draw in DrawType.objects.all():
                DrawSchedule.objects.get_or_create(zone=zone, draw_type=draw, defaults={'cutoff_time': default_cutoff})

        self.stdout.write(self.style.SUCCESS('Catálogo inicial cargado'))



