from django.contrib import admin

from .models import Category, Spot, SpotDetail, Tag


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "area", "noise_level", "status", "time_create")
    list_display_links = ("id", "title")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("category", "area", "noise_level", "status")
    search_fields = ("title", "content", "area", "category__name", "tags__name")
    filter_horizontal = ("tags",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    list_display_links = ("id", "name")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    list_display_links = ("id", "name")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(SpotDetail)
class SpotDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "seats", "has_wifi", "avg_stay_minutes", "work_hours")
    list_display_links = ("id", "spot")
    list_filter = ("has_wifi",)
