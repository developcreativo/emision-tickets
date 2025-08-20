from django.conf import settings
from django.db import models


class Ticket(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    zone = models.ForeignKey('catalog.Zone', on_delete=models.PROTECT)
    draw_type = models.ForeignKey('catalog.DrawType', on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_pieces = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"Ticket #{self.pk} - {self.zone} - {self.draw_type}"


class TicketItem(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='items')
    number = models.CharField(max_length=2)
    pieces = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('ticket', 'number')

    def __str__(self) -> str:
        return f"{self.number} x {self.pieces}"



