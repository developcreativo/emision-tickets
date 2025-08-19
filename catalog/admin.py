from django.contrib import admin

from .models import DrawSchedule, DrawType, NumberLimit, Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(DrawType)
class DrawTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(DrawSchedule)
class DrawScheduleAdmin(admin.ModelAdmin):
    list_display = ("zone", "draw_type", "cutoff_time", "is_active")
    list_filter = ("zone", "draw_type", "is_active")


@admin.register(NumberLimit)
class NumberLimitAdmin(admin.ModelAdmin):
    list_display = ("zone", "draw_type", "number", "max_pieces")
    list_filter = ("zone", "draw_type")
    search_fields = ("number",)



