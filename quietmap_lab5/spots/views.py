from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from .data import build_base_context, get_current_year
from .forms import SpotModelForm, SpotPlainForm, UploadFileForm
from .models import Category, Spot, Tag
from .uploads import save_uploaded_file

NOISE_QUERY_MAP = {
    "low": Spot.NoiseLevel.LOW,
    "medium": Spot.NoiseLevel.MEDIUM,
    "high": Spot.NoiseLevel.HIGH,
}

SORT_QUERY_MAP = {
    "new": ("-time_create", "id"),
    "old": ("time_create", "id"),
    "title": ("title", "id"),
}

SORT_LABEL_MAP = {
    "new": "сначала новые",
    "old": "сначала старые",
    "title": "по названию",
}


def index(request):
    search_query = request.GET.get("q", "").strip()
    spots = Spot.published.select_related("category").prefetch_related("tags", "detail")
    if search_query:
        spots = spots.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(tags__name__icontains=search_query)
            | Q(category__name__icontains=search_query)
        ).distinct()

    data = build_base_context("Карта тихих мест")
    data["spots"] = spots
    data["search_query"] = search_query
    data["stats"] = {
        "all": spots.count(),
        "areas": spots.values("area_slug").distinct().count(),
        "categories": Category.objects.count(),
        "tags": Tag.objects.count(),
    }
    return render(request, "spots/index.html", data)


def about(request):
    data = build_base_context("О проекте")
    data["project_description"] = (
        "Учебный Django-проект по теме «Карта тихих мест» для демонстрации "
        "связей между таблицами, тегов и ORM-запросов."
    )
    data["relations_hint"] = {
        "fk": "Spot -> Category (ForeignKey)",
        "m2m": "Spot <-> Tag (ManyToManyField)",
        "o2o": "Spot -> SpotDetail (OneToOneField)",
    }
    return render(request, "spots/about.html", data)


def forms_hub(request):
    data = build_base_context("Формы ЛР10")
    data["form_cards"] = [
        {
            "title": "Обычная форма",
            "description": "Форма без привязки к модели. Запись Spot создается вручную в коде представления.",
            "url_name": "plain_spot_add",
        },
        {
            "title": "ModelForm",
            "description": "Форма, связанная с моделью Spot, с загрузкой изображения и сохранением записи в БД.",
            "url_name": "model_spot_add",
        },
        {
            "title": "Загрузка файлов",
            "description": "Отдельная форма для загрузки файлов на сервер со случайными именами.",
            "url_name": "upload_file",
        },
    ]
    return render(request, "spots/forms_hub.html", data)


def plain_spot_add(request):
    if request.method == "POST":
        form = SpotPlainForm(request.POST)
        if form.is_valid():
            spot = form.save()
            messages.success(
                request,
                f"Обычная форма успешно создала запись «{spot.title}».",
            )
            if spot.status == Spot.PublicationStatus.PUBLISHED:
                return redirect(spot.get_absolute_url())
            return redirect("home")
    else:
        form = SpotPlainForm()

    data = build_base_context("Обычная форма добавления места")
    data["form"] = form
    data["submit_label"] = "Создать запись вручную"
    data["form_mode"] = "plain"
    return render(request, "spots/spot_form_plain.html", data)


def model_spot_add(request):
    if request.method == "POST":
        form = SpotModelForm(request.POST, request.FILES)
        if form.is_valid():
            spot = form.save()
            messages.success(
                request,
                f"ModelForm успешно сохранила запись «{spot.title}».",
            )
            if spot.status == Spot.PublicationStatus.PUBLISHED:
                return redirect(spot.get_absolute_url())
            return redirect("home")
    else:
        form = SpotModelForm()

    data = build_base_context("ModelForm для добавления места")
    data["form"] = form
    data["submit_label"] = "Сохранить через ModelForm"
    data["form_mode"] = "model"
    return render(request, "spots/spot_form_model.html", data)


def upload_file(request):
    uploaded_file_data = None

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            original_name = form.cleaned_data["file"].name
            relative_path = save_uploaded_file(form.cleaned_data["file"])
            uploaded_file_data = {
                "original_name": original_name,
                "saved_path": relative_path,
                "url": f"{settings.MEDIA_URL}{relative_path}",
                "description": form.cleaned_data["description"],
            }
            messages.success(
                request,
                f"Файл «{original_name}» сохранен как «{relative_path}».",
            )
            form = UploadFileForm()
    else:
        form = UploadFileForm()

    data = build_base_context("Загрузка файлов")
    data["form"] = form
    data["uploaded_file_data"] = uploaded_file_data
    data["submit_label"] = "Загрузить файл"
    return render(request, "spots/upload_file.html", data)


def spot_detail(request, spot_slug: str):
    try:
        spot = (
            Spot.published.select_related("category", "detail")
            .prefetch_related("tags")
            .get(slug=spot_slug)
        )
    except Spot.DoesNotExist as exc:
        raise Http404("Место не найдено") from exc

    data = build_base_context(f"Тихое место: {spot.title}")
    data["spot"] = spot
    data["related_spots"] = (
        Spot.published.filter(category=spot.category)
        .exclude(pk=spot.pk)
        .select_related("category")
        .prefetch_related("tags")[:3]
    )
    return render(request, "spots/spot_detail.html", data)


def area(request, area_slug: str):
    area_spots = (
        Spot.published.filter(area_slug=area_slug)
        .select_related("category")
        .prefetch_related("tags", "detail")
    )
    if not area_spots.exists():
        raise Http404("Район не найден")

    noise_filter = request.GET.get("noise")
    if noise_filter not in NOISE_QUERY_MAP:
        noise_filter = ""
    tag_filter = request.GET.get("tag", "").strip()
    sort_filter = request.GET.get("sort", "new")
    if sort_filter not in SORT_QUERY_MAP:
        sort_filter = "new"

    filtered_spots = area_spots
    if noise_filter:
        filtered_spots = filtered_spots.filter(noise_level=NOISE_QUERY_MAP[noise_filter])
    if tag_filter:
        filtered_spots = filtered_spots.filter(tags__slug=tag_filter)
    filtered_spots = filtered_spots.order_by(*SORT_QUERY_MAP[sort_filter]).distinct()
    area_name = area_spots.values_list("area", flat=True).first()

    data = build_base_context(f"Район: {area_name}")
    data["spots"] = filtered_spots
    data["area"] = area_name
    data["area_slug"] = area_slug
    data["area_tags"] = (
        Tag.objects.filter(spots__area_slug=area_slug)
        .annotate(total=Count("spots"))
        .order_by("name")
        .distinct()
    )
    data["filters"] = {
        "noise": noise_filter,
        "tag": tag_filter,
        "tag_name": (
            Tag.objects.filter(slug=tag_filter).values_list("name", flat=True).first()
            if tag_filter
            else ""
        ),
        "sort": sort_filter,
        "sort_label": SORT_LABEL_MAP[sort_filter],
    }
    return render(request, "spots/area.html", data)


def category(request, category_slug: str):
    try:
        category_obj = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist as exc:
        raise Http404("Категория не найдена") from exc

    spots = (
        Spot.published.filter(category=category_obj)
        .select_related("category")
        .prefetch_related("tags", "detail")
    )

    data = build_base_context(f"Категория: {category_obj.name}")
    data["category_obj"] = category_obj
    data["spots"] = spots
    return render(request, "spots/category.html", data)


def tags_index(request):
    tags = Tag.objects.annotate(total=Count("spots")).filter(total__gt=0).order_by("-total", "name")
    data = build_base_context("Теги")
    data["tags"] = tags
    return render(request, "spots/tags_index.html", data)


def tag(request, tag_slug: str):
    try:
        tag_obj = Tag.objects.annotate(total=Count("spots")).get(slug=tag_slug)
    except Tag.DoesNotExist as exc:
        raise Http404("Тег не найден") from exc

    spots = (
        Spot.published.filter(tags=tag_obj)
        .select_related("category")
        .prefetch_related("tags", "detail")
        .order_by("-time_create")
    )

    data = build_base_context(f"Тег: {tag_obj.name}")
    data["tag_obj"] = tag_obj
    data["spots"] = spots
    return render(request, "spots/tag.html", data)


def archive(request, year: int):
    current_year = get_current_year()
    if year > current_year:
        return redirect("home")

    data = build_base_context(f"Архив до {year} года")
    data["year"] = year
    data["spots"] = (
        Spot.published.filter(time_create__year__lte=year)
        .select_related("category")
        .prefetch_related("tags")
    )
    return render(request, "spots/archive.html", data)


def archive_404(request, year: int):
    current_year = get_current_year()
    if year > current_year:
        raise Http404("Архив за этот год недоступен")

    data = build_base_context(f"Архив (режим 404) до {year} года")
    data["year"] = year
    data["spots"] = (
        Spot.published.filter(time_create__year__lte=year)
        .select_related("category")
        .prefetch_related("tags")
    )
    return render(request, "spots/archive.html", data)


def page_not_found(request, exception):
    data = build_base_context("Страница не найдена")
    data["requested_path"] = request.path
    return render(request, "spots/404.html", data, status=404)
