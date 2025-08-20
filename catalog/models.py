from django.db import models


class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return self.name


class DrawType(models.Model):
    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class DrawSchedule(models.Model):
    draw_type = models.ForeignKey(
        DrawType, on_delete=models.CASCADE, related_name="schedules"
    )
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="schedules")
    cutoff_time = models.TimeField(
        help_text="Hora de cierre de jugadas para este sorteo en esta zona"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("draw_type", "zone")

    def __str__(self) -> str:
        formatted_time = self.cutoff_time.strftime("%H:%M") if self.cutoff_time else ""
        return f"{self.zone} - {self.draw_type} ({formatted_time})"


class NumberLimit(models.Model):
    draw_type = models.ForeignKey(DrawType, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    number = models.CharField(max_length=2)
    max_pieces = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("draw_type", "zone", "number")

    def __str__(self) -> str:
        return f"{self.zone}-{self.draw_type} #{self.number}: {self.max_pieces}"
