from django.contrib import admin, messages
from django.db.models import Count

from .models import Category, Spot, SpotDetail, Tag


class NoiseComfortFilter(admin.SimpleListFilter):
    title = "Комфорт по шуму"
    parameter_name = "comfort"

    def lookups(self, request, model_admin):
        return (
            ("quiet", "Тихие места"),
            ("not_quiet", "Средний/высокий шум"),
        )

    def queryset(self, request, queryset):
        if self.value() == "quiet":
            return queryset.filter(noise_level=Spot.NoiseLevel.LOW)
        if self.value() == "not_quiet":
            return queryset.exclude(noise_level=Spot.NoiseLevel.LOW)
        return queryset


class SpotDetailInline(admin.StackedInline):
    model = SpotDetail
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("seats", "has_wifi", "avg_stay_minutes", "work_hours")


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "area",
        "noise_level",
        "status",
        "brief_info",
        "tag_list",
        "detail_summary",
        "time_create",
    )
    list_display_links = ("title",)
    list_editable = ("noise_level", "status")
    list_filter = (NoiseComfortFilter, "category", "area", "noise_level", "status")
    search_fields = ("title", "content", "area", "category__name", "tags__name")
    ordering = ("-time_create", "title")
    list_per_page = 5
    date_hierarchy = "time_create"
    list_select_related = ("category",)
    prepopulated_fields = {"slug": ("title",), "area_slug": ("area",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("time_create", "time_update")
    save_on_top = True
    actions = ("set_published", "set_draft")
    inlines = (SpotDetailInline,)
    fieldsets = (
        ("Основная информация", {
            "fields": ("title", "slug", "content", "category", "tags"),
        }),
        ("Расположение и параметры", {
            "fields": ("area", "area_slug", "noise_level", "status"),
        }),
        ("Служебные поля", {
            "fields": ("time_create", "time_update"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("tags").select_related("category", "detail")

    @admin.display(description="Краткое описание", ordering="content")
    def brief_info(self, spot):
        return f"{len(spot.content)} символов"

    @admin.display(description="Теги")
    def tag_list(self, spot):
        tags = [tag.name for tag in spot.tags.all()]
        return ", ".join(tags) if tags else "без тегов"

    @admin.display(description="Детали места")
    def detail_summary(self, spot):
        if not hasattr(spot, "detail"):
            return "не заполнено"
        wifi = "Wi-Fi" if spot.detail.has_wifi else "без Wi-Fi"
        return f"{spot.detail.seats} мест, {wifi}"

    @admin.action(description="Опубликовать выбранные места")
    def set_published(self, request, queryset):
        updated = queryset.update(status=Spot.PublicationStatus.PUBLISHED)
        self.message_user(
            request,
            f"Опубликовано записей: {updated}.",
            messages.SUCCESS,
        )

    @admin.action(description="Перевести выбранные места в черновики")
    def set_draft(self, request, queryset):
        updated = queryset.update(status=Spot.PublicationStatus.DRAFT)
        self.message_user(
            request,
            f"Переведено в черновики записей: {updated}.",
            messages.WARNING,
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "spot_count")
    list_display_links = ("id", "name")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_spots=Count("spots"))

    @admin.display(description="Количество мест", ordering="total_spots")
    def spot_count(self, category):
        return category.total_spots


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "spot_count")
    list_display_links = ("id", "name")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_spots=Count("spots"))

    @admin.display(description="Количество мест", ordering="total_spots")
    def spot_count(self, tag):
        return tag.total_spots


@admin.register(SpotDetail)
class SpotDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "seats", "has_wifi", "avg_stay_minutes", "work_hours")
    list_display_links = ("id", "spot")
    list_filter = ("has_wifi",)
    search_fields = ("spot__title", "spot__area")
    autocomplete_fields = ("spot",)
