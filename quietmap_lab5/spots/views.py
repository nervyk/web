from django.http import Http404
from django.shortcuts import redirect, render

from .data import build_base_context, get_current_year
from .models import Spot

NOISE_QUERY_MAP = {
    "low": Spot.NoiseLevel.LOW,
    "medium": Spot.NoiseLevel.MEDIUM,
    "high": Spot.NoiseLevel.HIGH,
}


def index(request):
    spots = Spot.published.all()
    data = build_base_context("Карта тихих мест")
    data["spots"] = spots
    data["stats"] = {
        "all": spots.count(),
        "areas": spots.values("area_slug").distinct().count(),
    }
    return render(request, "spots/index.html", data)


def about(request):
    data = build_base_context("О проекте")
    data["project_description"] = (
        "Учебный Django-проект для демонстрации шаблонов, фильтров, тегов и статики."
    )
    return render(request, "spots/about.html", data)


def spot_detail(request, spot_slug: str):
    try:
        spot = Spot.published.get(slug=spot_slug)
    except Spot.DoesNotExist as exc:
        raise Http404("Место не найдено") from exc

    data = build_base_context(f"Тихое место: {spot.title}")
    data["spot"] = spot
    return render(request, "spots/spot_detail.html", data)


def area(request, area_slug: str):
    area_spots = Spot.published.filter(area_slug=area_slug)
    if not area_spots.exists():
        raise Http404("Район не найден")

    noise_filter = request.GET.get("noise")
    filtered_spots = area_spots
    if noise_filter in NOISE_QUERY_MAP:
        filtered_spots = area_spots.filter(noise_level=NOISE_QUERY_MAP[noise_filter])
    area_name = area_spots.values_list("area", flat=True).first()

    data = build_base_context(f"Район: {area_name}")
    data["spots"] = filtered_spots
    data["area"] = area_name
    data["filters"] = {
        "noise": noise_filter,
        "time": request.GET.get("time"),
    }
    return render(request, "spots/area.html", data)


def archive(request, year: int):
    current_year = get_current_year()
    if year > current_year:
        return redirect("home")

    data = build_base_context(f"Архив до {year} года")
    data["year"] = year
    data["spots"] = Spot.published.filter(time_create__year__lte=year)
    return render(request, "spots/archive.html", data)


def archive_404(request, year: int):
    current_year = get_current_year()
    if year > current_year:
        raise Http404("Архив за этот год недоступен")

    data = build_base_context(f"Архив (режим 404) до {year} года")
    data["year"] = year
    data["spots"] = Spot.published.filter(time_create__year__lte=year)
    return render(request, "spots/archive.html", data)


def page_not_found(request, exception):
    data = build_base_context("Страница не найдена")
    data["requested_path"] = request.path
    return render(request, "spots/404.html", data, status=404)
