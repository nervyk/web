from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, F, Max, Min, Q, Value
from django.db.models.functions import Length

from spots.models import Category, Spot, Tag


class Command(BaseCommand):
    help = (
        "Демонстрация ORM-операций для ЛР8: связи моделей, Q/F/Value, "
        "вычисляемые поля, агрегации, группировка и values()."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO LAB8: RELATIONS =="))

        sample = Spot.published.select_related("category", "detail").prefetch_related("tags").first()
        if not sample:
            self.stdout.write(self.style.ERROR("Нет данных в Spot. Сначала добавьте записи."))
            return

        self.stdout.write(
            "Spot -> Category (FK): "
            f"'{sample.title}' -> '{sample.category.name}'"
        )
        self.stdout.write(
            "Spot -> SpotDetail (O2O): "
            f"мест={sample.detail.seats}, wifi={'да' if sample.detail.has_wifi else 'нет'}"
        )
        self.stdout.write(
            "Spot <-> Tag (M2M): " + ", ".join(sample.tags.values_list("slug", flat=True))
        )

        self.stdout.write(self.style.MIGRATE_HEADING("== Q FILTER =="))
        q_rows = list(
            Spot.published.filter(
                Q(noise_level=Spot.NoiseLevel.LOW) | Q(tags__slug="coworking")
            )
            .distinct()
            .values("slug", "noise_level")
        )
        self.stdout.write(str(q_rows))

        self.stdout.write(self.style.MIGRATE_HEADING("== F FILTER =="))
        f_rows = list(
            Spot.published.filter(id__gte=F("noise_level"))
            .values("id", "slug", "noise_level")
            .order_by("id")
        )
        self.stdout.write(str(f_rows))

        self.stdout.write(self.style.MIGRATE_HEADING("== VALUE + ANNOTATE =="))
        value_rows = list(
            Spot.published.annotate(source=Value("lab8")).values("slug", "source")[:3]
        )
        self.stdout.write(str(value_rows))

        self.stdout.write(self.style.MIGRATE_HEADING("== CALCULATED FIELDS + DB FUNCTION =="))
        calc_rows = list(
            Spot.published.annotate(
                title_len=Length("title"),
                comfort_score=F("detail__seats") - F("noise_level") * 2,
            )
            .values("slug", "title_len", "comfort_score")
            .order_by("-comfort_score", "slug")
        )
        self.stdout.write(str(calc_rows))

        self.stdout.write(self.style.MIGRATE_HEADING("== AGGREGATE =="))
        agg = Spot.published.aggregate(
            total=Count("id"),
            avg_noise=Avg("noise_level"),
            max_noise=Max("noise_level"),
            min_noise=Min("noise_level"),
        )
        self.stdout.write(str(agg))

        self.stdout.write(self.style.MIGRATE_HEADING("== GROUP BY CATEGORY =="))
        grouped = list(
            Category.objects.annotate(total=Count("spots"))
            .values("name", "slug", "total")
            .order_by("-total", "name")
        )
        self.stdout.write(str(grouped))

        self.stdout.write(self.style.MIGRATE_HEADING("== VALUES FROM RELATED TABLES =="))
        related_values = list(
            Spot.published.values(
                "title",
                "category__name",
                "detail__work_hours",
            ).order_by("id")
        )
        self.stdout.write(str(related_values))

        self.stdout.write(self.style.MIGRATE_HEADING("== EXISTS / COUNT =="))
        used_tags = Tag.objects.annotate(total=Count("spots")).filter(total__gt=0)
        self.stdout.write(
            f"used_tags.exists()={used_tags.exists()} | used_tags.count()={used_tags.count()}"
        )

        self.stdout.write(self.style.SUCCESS("ЛР8: демонстрация ORM-команд завершена успешно."))
