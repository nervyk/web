from django import template

from spots.models import Spot

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
    recent = Spot.published.order_by("-time_create")[:limit]
    return {"recent_spots": recent}
