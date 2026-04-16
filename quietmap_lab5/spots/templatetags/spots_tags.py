from django import template
from django.db.models import Count

from spots.models import Category, Spot, Tag

register = template.Library()


@register.simple_tag
def noise_badge(level: str) -> str:
    labels = {
        Spot.NoiseLevel.LOW: "низкий",
        Spot.NoiseLevel.MEDIUM: "средний",
        Spot.NoiseLevel.HIGH: "высокий",
        "low": "низкий",
        "medium": "средний",
        "high": "высокий",
    }
    return labels.get(level, "неизвестный")


@register.filter
def noise_class(level: str) -> str:
    classes = {
        Spot.NoiseLevel.LOW: "noise-low",
        Spot.NoiseLevel.MEDIUM: "noise-medium",
        Spot.NoiseLevel.HIGH: "noise-high",
        "low": "noise-low",
        "medium": "noise-medium",
        "high": "noise-high",
    }
    return classes.get(level, "noise-unknown")


@register.inclusion_tag("spots/includes/recent_spots.html")
def show_recent_spots(limit: int = 2) -> dict:
    recent = (
        Spot.published.select_related("category")
        .prefetch_related("tags")
        .order_by("-time_create")[:limit]
    )
    return {"recent_spots": recent}


@register.inclusion_tag("spots/includes/list_categories.html")
def show_categories() -> dict:
    categories = Category.objects.annotate(total=Count("spots")).filter(total__gt=0).order_by("name")
    return {"categories": categories}


@register.inclusion_tag("spots/includes/list_tags.html")
def show_all_tags(limit: int = 12) -> dict:
    tags = Tag.objects.annotate(total=Count("spots")).filter(total__gt=0).order_by("-total", "name")[:limit]
    return {"tags": tags}
