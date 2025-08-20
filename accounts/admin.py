from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "zone", "is_active")
    list_filter = ("role", "zone", "is_active")
    search_fields = ("username", "email")



