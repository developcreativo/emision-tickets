import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea un usuario admin por defecto si no existe'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('ADMIN_USER', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin1234')

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(username=username, email=email, password=password)
            user.role = 'ADMIN'
            user.save(update_fields=['role'])
            self.stdout.write(self.style.SUCCESS(f'Admin creado: {username}'))
        else:
            self.stdout.write('Admin por defecto ya existe')



