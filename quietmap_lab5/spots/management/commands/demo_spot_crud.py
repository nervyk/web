from django.core.management.base import BaseCommand

from spots.models import Spot


class Command(BaseCommand):
    help = (
        "Демонстрация CRUD-операций, выборки, фильтрации и сортировки "
        "для лабораторной работы №7."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("== DEMO: CREATE =="))
        Spot.objects.filter(slug="lab7-crud-temp").delete()
        spot = Spot.objects.create(
            title="Тестовая локация ЛР7",
            slug="lab7-crud-temp",
            content="Временная запись для демонстрации CRUD-операций.",
            area="Тестовый район",
            area_slug="test-area",
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.DRAFT,
        )
        self.stdout.write(f"Создана запись id={spot.id}, slug={spot.slug}")

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
        deleted_count, _ = Spot.objects.filter(slug="lab7-crud-temp").delete()
        self.stdout.write(f"Удалено записей: {deleted_count}")

        self.stdout.write(self.style.SUCCESS("CRUD-демонстрация завершена успешно."))
