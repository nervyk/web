from django.contrib import admin

from .models import Spot


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "area", "noise_level", "status", "time_create")
    list_display_links = ("id", "title")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("area", "noise_level", "status")
    search_fields = ("title", "content", "area")
