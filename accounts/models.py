from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        SELLER = 'SELLER', 'Vendedor'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.SELLER)
    zone = models.ForeignKey('catalog.Zone', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"



