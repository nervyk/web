from django.core.management.base import BaseCommand

from spots.models import Category, Spot, SpotDetail, Tag


class Command(BaseCommand):
    help = (
        "Демонстрация CRUD-операций, выборки, фильтрации и сортировки "
        "для лабораторной работы №7."
    )

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug="lab7-temp-category",
            defaults={"name": "Техническая категория"},
        )
        tag, _ = Tag.objects.get_or_create(
            slug="lab7-temp-tag",
            defaults={"name": "Технический тег"},
        )

        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: CREATE =="))
        Spot.objects.filter(slug__in=["lab7-crud-temp", "lab7-crud-temp-2"]).delete()
        spot = Spot.objects.create(
            title="Тестовая локация ЛР7",
            slug="lab7-crud-temp",
            content="Временная запись для демонстрации CRUD-операций.",
            area="Тестовый район",
            area_slug="test-area",
            category=category,
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.DRAFT,
        )
        spot.tags.add(tag)
        SpotDetail.objects.update_or_create(
            spot=spot,
            defaults={
                "seats": 10,
                "has_wifi": True,
                "avg_stay_minutes": 70,
                "work_hours": "09:00-21:00",
            },
        )
        self.stdout.write(f"Создана запись id={spot.id}, slug={spot.slug}")

        spot_2 = Spot.objects.create(
            title="Тестовая локация ЛР7 (2)",
            slug="lab7-crud-temp-2",
            content="Вторая запись для демонстрации фильтрации и сортировки.",
            area="Центр",
            area_slug="center",
            category=category,
            noise_level=Spot.NoiseLevel.HIGH,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        spot_2.tags.add(tag)
        SpotDetail.objects.update_or_create(
            spot=spot_2,
            defaults={
                "seats": 6,
                "has_wifi": True,
                "avg_stay_minutes": 45,
                "work_hours": "08:00-22:00",
            },
        )
        self.stdout.write(f"Создана запись id={spot_2.id}, slug={spot_2.slug}")

        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: READ =="))
        fetched = Spot.objects.get(slug="lab7-crud-temp")
        self.stdout.write(
            f"Выбрана запись: title='{fetched.title}', status={fetched.get_status_display()}"
        )

        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: UPDATE =="))
        fetched.status = Spot.PublicationStatus.PUBLISHED
        fetched.noise_level = Spot.NoiseLevel.LOW
        fetched.content = "Запись обновлена в рамках демонстрации update."
        fetched.save()
        self.stdout.write(
            f"Обновлена запись id={fetched.id}, status={fetched.get_status_display()}"
        )

        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: FILTER + SORT =="))
        filtered = Spot.published.filter(area_slug="center").order_by("-time_create")
        self.stdout.write(
            "Опубликованные записи из района center (от новых к старым): "
            + ", ".join(filtered.values_list("slug", flat=True))
        )

        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: DELETE =="))
        deleted_count, deleted_map = Spot.objects.filter(
            slug__in=["lab7-crud-temp", "lab7-crud-temp-2"]
        ).delete()
        self.stdout.write(
            "Удалено записей Spot: "
            f"{deleted_map.get('spots.Spot', 0)} (всего удалено объектов: {deleted_count})"
        )

        if not Spot.objects.filter(category=category).exists():
            category.delete()
        if not tag.spots.exists():
            tag.delete()

        self.stdout.write(self.style.SUCCESS("CRUD-демонстрация завершена успешно."))
